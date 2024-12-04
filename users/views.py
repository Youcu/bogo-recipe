### in users_views.py ###

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from allauth.account.views import ConfirmEmailView
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.utils import send_email_confirmation
from allauth.account.models import EmailAddress
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from allauth.account.forms import ResetPasswordForm
from django.core.exceptions import ValidationError
from allauth.account.views import ConfirmEmailView
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from django.http import HttpResponseRedirect
from django.db import transaction, IntegrityError
from django.db import connection
from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken, AccessToken
from datetime import datetime, date
from django.utils.timezone import now
from .serializers import UserSerializer
from users.models import (
    User,
    UserLevel,
    ExceptIngreList,
    UserIngreList,
    Bookmark,
    History,
    Bookmark,
)
from base.models import (
    IngreList,
    IngreLocDict,
)
from rest_framework.pagination import PageNumberPagination
from recipes.models import (
    Recipe, 
    RecipeThumbSrc, 
    RecipeVideoSrc, 
    RecipeProgress, 
    RecipeCategory, 
    RecipeMainIngre
)

class CustomConfirmEmailView(ConfirmEmailView):
    def get(self, request, *args, **kwargs):
        """
        이메일 인증 화면 렌더링
        """
        confirmation = self.get_object()  # 이메일 확인 객체 가져오기
        if confirmation:
            context = {"email": confirmation.email_address.email}
            return render(request, "account/email_confirm.html", context)
        return Response({"error": "Invalid confirmation key."}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        """
        이메일 인증 처리, 계정 활성화 및 완료 페이지로 리다이렉트
        """
        try:
            # 이메일 인증 로직 처리
            confirmation = self.get_object()
            confirmation.confirm(self.request)  # 인증 완료 처리
            
            # 사용자 계정 활성화
            email = confirmation.email_address.email
            user = User.objects.get(email=email)

            if not user.is_active:
                user.is_active = True
                user.save()

                # JWT 토큰 발급
                refresh = RefreshToken.for_user(user)
                
                # JSON 요청인 경우 JSON 응답 반환
                if request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
                    return Response({
                        "message": "Email confirmed. Account activated.",
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }, status=status.HTTP_200_OK)

                # HTML 요청인 경우 완료 페이지로 리다이렉트
                return HttpResponseRedirect("/accounts/email-confirm-complete/")

            # 이미 활성화된 경우
            if request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
                return Response({"message": "Account is already active."}, status=status.HTTP_200_OK)

            return HttpResponseRedirect("/accounts/email-confirm-complete/")

        except Exception as e:
            # 에러 처리
            if request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return render(request, "account/email_confirm_failed.html", {"error": str(e)})

    def get_object(self, queryset=None):
        """
        이메일 인증 키 확인
        """
        key = self.kwargs['key']
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if not email_confirmation:
            if queryset is None:
                queryset = self.get_queryset()
            try:
                email_confirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                email_confirmation = None
        return email_confirmation

User = get_user_model()

class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            email = data.get("email")
            password = data.get("password")
            name = data.get("name")
            gender = data.get("gender")
            convenience = data.get("convenience", False)

            # 필수 필드 검증
            if not email or not password:
                return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

            # 이메일 중복 확인
            if User.objects.filter(email=email).exists():
                return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

            # 사용자 계정 생성 (비활성화 상태)
            user = User.objects.create_user(
                email=email,
                password=password,
                name=name,
                gender=gender,
                convenience=convenience,
                is_active=False,  # 이메일 인증 전 비활성화
            )

            # 이메일 인증 요청
            send_email_confirmation(request, user)

            return Response({
                "message": "User created successfully. Please confirm your email to activate your account."
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SignInView(APIView):
    permission_classes = [AllowAny]  # 로그인은 인증 없이 허용

    def post(self, request):
        try:
            data = request.data
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

            # 사용자 인증
            user = authenticate(email=email, password=password)
            if user is None:
                print("Authentication failed.")
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            print(f"Authenticated user: {user.email}")

            # 이메일 인증 여부 확인
            if not EmailAddress.objects.filter(email=email, verified=True).exists():
                print("Email not verified.")
                return Response({"error": "Email not verified"}, status=status.HTTP_403_FORBIDDEN)

            print("Email is verified.")

            # JWT 토큰 발급
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            print(f"Generated tokens: Refresh - {str(refresh)}, Access - {access_token}")

            return Response({
                "refresh": str(refresh),
                "access": access_token,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Exception occurred: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetView(APIView):
    permission_classes = [AllowAny]  # 인증 없이 접근 가능
    
    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            form = ResetPasswordForm(data={"email": email})
            if form.is_valid():
                form.save(request)
                return Response({"message": "Password reset email sent"}, status=status.HTTP_200_OK)
            return Response({"error": form.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserAccountUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            return Response({
                'email': user.email,
                'name': user.name,
                'gender': user.gender,
                'convenience': user.convenience,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            user = request.user

            # 필수값이 있는 경우 검증
            name = request.data.get('name', user.name)
            gender = request.data.get('gender', user.gender)
            convenience = request.data.get('convenience', user.convenience)

            # 예외 처리: 유효하지 않은 값 검증
            if gender and gender not in ['M', 'F', None]:
                return Response({"error": "Invalid gender value. Use 'M', 'F', or leave it blank."},
                                status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(convenience, bool) and convenience is not None:
                return Response({"error": "Convenience must be a boolean value (True/False)."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 필드 업데이트
            user.name = name
            user.gender = gender
            user.convenience = convenience
            user.save()

            return Response({'message': 'User updated successfully.'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        user = request.user

        try:
            # 연결된 데이터 삭제
            UserLevel.objects.filter(user=user).delete()
            ExceptIngreList.objects.filter(user=user).delete()
            UserIngreList.objects.filter(user=user).delete()
            Bookmark.objects.filter(user=user).delete()
            History.objects.filter(user=user).delete()

            # JWT 토큰 블랙리스트 처리
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            # User 삭제
            user.delete()

            return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            # 예외 발생 시 롤백 및 에러 응답
            transaction.rollback()
            return Response(
                {"error": f"Failed to delete account: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
       
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request, *args, **kwargs):
        try:
            user = request.user  # 현재 요청한 사용자
            serializer = UserSerializer(user)  # 직렬화 수행
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AttributeError as e:
            # 유효하지 않은 사용자 정보로 인한 예외 처리
            return Response({"error": "User data is incomplete or invalid."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 기타 예외 처리
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user  # 현재 요청을 보낸 유저

            # 유저의 모든 OutstandingToken을 조회
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                # 각 토큰을 블랙리스트에 추가
                _, _ = BlacklistedToken.objects.get_or_create(token=token)

            return Response({"message": "All tokens blacklisted successfully. Logout completed."},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Logout failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

### User Ingre List APIs ###
class UserIngreListView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능

    def post(self, request):
        """
        사용자가 보유한 재료를 저장합니다.
        """
        user = request.user
        data = request.data

        ingre_id_lst = data.get("ingre_id_lst", [])
        user_ingre_amount_lst = data.get("user_ingre_amount_lst", [])
        expiry_lst = data.get("expiry_lst", [])
        ingre_loc_lst = data.get("ingre_loc_lst", [])

        if not (len(ingre_id_lst) == len(user_ingre_amount_lst) == len(expiry_lst) == len(ingre_loc_lst)):
            return Response({"error": "Input data lengths do not match."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                for idx, ingre_id in enumerate(ingre_id_lst):
                    # 날짜 문자열 -> datetime.date 객체로 변환
                    try:
                        expiry_date = datetime.strptime(expiry_lst[idx], "%Y-%m-%d").date()
                    except ValueError:
                        return Response({"error": f"Invalid date format for expiry: {expiry_lst[idx]}"}, 
                                        status=status.HTTP_400_BAD_REQUEST)

                    ingre = IngreList.objects.get(pk=ingre_id)  # 재료 ID로 IngreList 조회
                    ingre_loc = IngreLocDict.objects.get(pk=ingre_loc_lst[idx])  # 위치 ID로 IngreLocDict 조회

                    # 기존 데이터가 있으면 업데이트, 없으면 생성
                    obj, created = UserIngreList.objects.update_or_create(
                        user=user,
                        ingre=ingre,
                        defaults={
                            "user_ingre_amount": user_ingre_amount_lst[idx],
                            "expiry": expiry_date,
                            "ingre_loc": ingre_loc,
                        }
                    )

                    # 우선순위 계산 및 업데이트
                    obj.calculate_priority()
                    UserIngreList.objects.filter(pk=obj.pk).update(priority=obj.priority)

            return Response({"message": "Ingredients saved successfully."}, status=status.HTTP_201_CREATED)
        except IngreList.DoesNotExist:
            return Response({"error": "One or more ingredients not found."}, status=status.HTTP_404_NOT_FOUND)
        except IngreLocDict.DoesNotExist:
            return Response({"error": "One or more locations not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        사용자가 보유한 특정 재료를 삭제합니다.
        """
        user = request.user
        ingre_id = request.data.get("ingre_id")

        if not ingre_id:
            return Response({"error": "Ingredient ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ingre = IngreList.objects.get(pk=ingre_id)
            obj = UserIngreList.objects.get(user=user, ingre=ingre)
            obj.delete()
            return Response({"message": "Ingredient deleted successfully."}, status=status.HTTP_200_OK)
        except IngreList.DoesNotExist:
            return Response({"error": "Ingredient not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserIngreList.DoesNotExist:
            return Response({"error": "Ingredient not associated with the user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        사용자가 보유한 모든 재료를 조회합니다.
        """
        user = request.user
        try:
            user_ingredients = UserIngreList.objects.filter(user=user)
            result = [
                {
                    "ingre_id": ingre.ingre.ingre_id,  # 여기서 ingre.ingre_id로 수정
                    "ingre_name": ingre.ingre.ingre_name,
                    "user_ingre_amount": ingre.user_ingre_amount,
                    "expiry": ingre.expiry,
                    "ingre_loc": ingre.ingre_loc.loc_name if ingre.ingre_loc else None,
                    "priority": ingre.priority,
                }
                for ingre in user_ingredients
            ]
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


##### Exception Ingre List APIs #####
class UserExceptIngreView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능

    def post(self, request):
        """
        사용자가 제외할 재료를 저장합니다.
        """
        user = request.user
        data = request.data
        ingre_id_lst = data.get("ingre_id_lst", [])

        if not ingre_id_lst:
            return Response({"error": "Ingredient ID list is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                for ingre_id in ingre_id_lst:
                    ingre = IngreList.objects.get(pk=ingre_id)  # 재료 ID로 IngreList 조회

                    # 기존 데이터가 있으면 무시, 없으면 생성
                    ExceptIngreList.objects.get_or_create(user=user, ingre=ingre)

            return Response({"message": "Excluded ingredients saved successfully."}, status=status.HTTP_201_CREATED)
        except IngreList.DoesNotExist:
            return Response({"error": "One or more ingredients not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        사용자가 제외한 모든 재료를 조회합니다.
        """
        user = request.user
        try:
            excluded_ingredients = ExceptIngreList.objects.filter(user=user)
            result = [
                {
                    "ingre_id": excl.ingre.ingre_id,
                    "ingre_name": excl.ingre.ingre_name
                }
                for excl in excluded_ingredients
            ]
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        사용자가 제외한 특정 재료를 삭제합니다.
        """
        user = request.user
        ingre_id = request.data.get("ingre_id")

        if not ingre_id:
            return Response({"error": "Ingredient ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ingre = IngreList.objects.get(pk=ingre_id)
            excl = ExceptIngreList.objects.get(user=user, ingre=ingre)
            excl.delete()
            return Response({"message": "Excluded ingredient deleted successfully."}, status=status.HTTP_200_OK)
        except IngreList.DoesNotExist:
            return Response({"error": "Ingredient not found."}, status=status.HTTP_404_NOT_FOUND)
        except ExceptIngreList.DoesNotExist:
            return Response({"error": "Ingredient not excluded by the user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


##### User Level APIs #####
class UserLevelView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능

    def post(self, request):
        """
        사용자의 레벨을 생성하거나 업데이트합니다.
        """
        user = request.user
        data = request.data
        user_level = data.get("level")

        if user_level is None:
            return Response({"error": "Level is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 레벨 검증
        if not isinstance(user_level, int) or user_level < 0 or user_level > 4:
            return Response({"error": "Level must be an integer between 0 and 4."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # UserLevel 생성 또는 업데이트
            obj, created = UserLevel.objects.update_or_create(
                user=user,
                defaults={"user_level": user_level},
            )
            message = "User level created successfully." if created else "User level updated successfully."
            return Response({"message": message}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        사용자의 현재 레벨을 조회합니다.
        """
        user = request.user
        try:
            user_level = UserLevel.objects.get(user=user)
            return Response({"level": user_level.user_level}, status=status.HTTP_200_OK)
        except UserLevel.DoesNotExist:
            return Response({"error": "User level not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """
        사용자의 레벨을 업데이트합니다.
        """
        user = request.user
        data = request.data
        user_level = data.get("level")

        if user_level is None:
            return Response({"error": "Level is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 레벨 검증
        if not isinstance(user_level, int) or user_level < 0 or user_level > 4:
            return Response({"error": "Level must be an integer between 0 and 4."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # UserLevel 업데이트
            obj = UserLevel.objects.get(user=user)
            obj.user_level = user_level
            obj.save()
            return Response({"message": "User level updated successfully."}, status=status.HTTP_200_OK)
        except UserLevel.DoesNotExist:
            return Response({"error": "User level not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


##### Bookmark APIs #####
class BookmarkPagination(PageNumberPagination):
    page_size = 10  # 페이지당 표시할 항목 수
    max_page_size = 100

class BookmarkView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능

    def post(self, request):
        """
        사용자가 특정 레시피를 북마크에 추가합니다.
        """
        user = request.user
        data = request.data
        recipe_id = data.get("recipe_id")

        if not recipe_id:
            return Response({"error": "Recipe ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipe = Recipe.objects.get(pk=recipe_id)  # 레시피 ID로 Recipe 객체 조회

            # 북마크가 이미 존재하면 무시
            obj, created = Bookmark.objects.get_or_create(user=user, recipe=recipe)

            if created:
                return Response({"message": "Recipe bookmarked successfully."}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Recipe is already bookmarked."}, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"error": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        사용자가 북마크한 모든 레시피를 조회합니다.
        """
        user = request.user
        paginator = BookmarkPagination()

        try:
            # 북마크된 레시피 ID 가져오기
            bookmarked_recipes = Bookmark.objects.filter(user=user).values_list("recipe_id", flat=True)

            # 북마크된 레시피를 가져오며 관련된 데이터를 Prefetch 및 Select 관련 설정
            queryset = Recipe.objects.filter(recipe_id__in=bookmarked_recipes).select_related(
                "recipethumbsrc",  # Thumbnail
                "recipevideosrc",  # Video source
                "recipetime",      # Cooking time
                "recipeamount",    # Amount (N인분)
                "recipelevel"      # Level (Difficulty)
            ).prefetch_related(
                "recipecategory_set",  # RecipeCategory
                "recipeingrelist_set",  # RecipeIngredients
                "recipemainingre_set",  # RecipeMainIngredients
                "recipeprogress_set"   # RecipeProgress
            )

            # 페이지네이션 처리
            page = paginator.paginate_queryset(queryset, request)

            # JSON 응답 형식 구성
            results = []
            for recipe in page:
                ingredients = recipe.recipeingrelist_set.all()
                main_ingredients = recipe.recipemainingre_set.all()
                categories = recipe.recipecategory_set.all()
                progress = recipe.recipeprogress_set.all()

                results.append({
                    "recipe_id": recipe.recipe_id,
                    "recipe_name": recipe.recipe_name,
                    "recipe_amount": getattr(recipe.recipeamount, "recipe_amount", None),
                    "recipe_level": getattr(recipe.recipelevel, "recipe_level", None),
                    "recipe_time": getattr(recipe.recipetime, "recipe_time", None),
                    "ingredients_title_lst": [i.ingre.ingre_name for i in ingredients],
                    "main_ingre": [m.main_ingre.ingre_name for m in main_ingredients],
                    "ingredients_amount_lst": [i.ingredients_amount_lst for i in ingredients],
                    "recipe_category": [c.recipe_category.recipe_category_name for c in categories],
                    "video_src": getattr(recipe.recipevideosrc, "video_src", None),
                    "thumb": getattr(recipe.recipethumbsrc, "thumb_src", None),
                    "recipe_progress_lst": [p.recipe_progress for p in progress],
                    "recipe_progress_img_lst": [p.recipe_img_src for p in progress],
                })

            return paginator.get_paginated_response(results)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        사용자의 북마크에서 특정 레시피를 제거합니다.
        """
        user = request.user
        recipe_id = request.data.get("recipe_id")

        if not recipe_id:
            return Response({"error": "Recipe ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipe = Recipe.objects.get(pk=recipe_id)
            bookmark = Bookmark.objects.get(user=user, recipe=recipe)
            bookmark.delete()
            return Response({"message": "Recipe removed from bookmarks."}, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"error": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
        except Bookmark.DoesNotExist:
            return Response({"error": "Bookmark not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

##### History APIs #####
class HistoryPagination(PageNumberPagination):
    page_size = 10  # 페이지당 표시할 항목 수
    max_page_size = 100

class HistoryView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능

    def post(self, request):
        """
        사용자가 레시피를 열람했을 때 열람 정보를 저장하거나 날짜를 업데이트합니다.
        """
        user = request.user
        data = request.data
        recipe_id = data.get("recipe_id")

        if not recipe_id:
            return Response({"error": "Recipe ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipe = Recipe.objects.get(pk=recipe_id)  # 레시피 ID로 Recipe 객체 조회

            # 기존 기록이 있으면 viewed_at 업데이트, 없으면 새로 생성
            obj, created = History.objects.update_or_create(
                user=user,
                recipe=recipe,
                defaults={"viewed_at": now()},
            )

            message = "History created successfully." if created else "History updated successfully."
            return Response({"message": message}, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response({"error": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        사용자가 열람했던 모든 레시피를 조회합니다.
        """
        user = request.user
        paginator = HistoryPagination()

        try:
            # 사용자의 열람 기록 가져오기
            history_recipes = History.objects.filter(user=user).order_by('-viewed_at').values_list("recipe_id", flat=True)

            # 열람 기록에 해당하는 레시피 데이터 가져오기
            queryset = Recipe.objects.filter(recipe_id__in=history_recipes).select_related(
                "recipethumbsrc",  # Thumbnail
                "recipevideosrc",  # Video source
                "recipetime",      # Cooking time
                "recipeamount",    # Amount (N인분)
                "recipelevel"      # Level (Difficulty)
            ).prefetch_related(
                "recipecategory_set",  # RecipeCategory
                "recipeingrelist_set",  # RecipeIngredients
                "recipemainingre_set",  # RecipeMainIngredients
                "recipeprogress_set"   # RecipeProgress
            )

            # 페이지네이션 처리
            page = paginator.paginate_queryset(queryset, request)

            # JSON 응답 형식 구성
            results = []
            for recipe in page:
                ingredients = recipe.recipeingrelist_set.all()
                main_ingredients = recipe.recipemainingre_set.all()
                categories = recipe.recipecategory_set.all()
                progress = recipe.recipeprogress_set.all()

                results.append({
                    "recipe_id": recipe.recipe_id,
                    "recipe_name": recipe.recipe_name,
                    "recipe_amount": getattr(recipe.recipeamount, "recipe_amount", None),
                    "recipe_level": getattr(recipe.recipelevel, "recipe_level", None),
                    "recipe_time": getattr(recipe.recipetime, "recipe_time", None),
                    "ingredients_title_lst": [i.ingre.ingre_name for i in ingredients],
                    "main_ingre": [m.main_ingre.ingre_name for m in main_ingredients],
                    "ingredients_amount_lst": [i.ingredients_amount_lst for i in ingredients],
                    "recipe_category": [c.recipe_category.recipe_category_name for c in categories],
                    "video_src": getattr(recipe.recipevideosrc, "video_src", None),
                    "thumb": getattr(recipe.recipethumbsrc, "thumb_src", None),
                    "recipe_progress_lst": [p.recipe_progress for p in progress],
                    "recipe_progress_img_lst": [p.recipe_img_src for p in progress],
                })

            return paginator.get_paginated_response(results)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        사용자가 열람 기록에서 특정 레시피를 제거합니다.
        """
        user = request.user
        recipe_id = request.data.get("recipe_id")

        if not recipe_id:
            return Response({"error": "Recipe ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipe = Recipe.objects.get(pk=recipe_id)
            history = History.objects.get(user=user, recipe=recipe)
            history.delete()
            return Response({"message": "History deleted successfully."}, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"error": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
        except History.DoesNotExist:
            return Response({"error": "History not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
