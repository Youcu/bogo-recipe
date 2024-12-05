### in recipes/views.py ###

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Subquery, OuterRef, Prefetch, Count, F, Q, FloatField, ExpressionWrapper, Sum
from django.db.models.functions import Coalesce
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from recipes.models import (
    Recipe,
    RecipeIngreList,
    RecipeMainIngre,
    RecipeProgress,
    RecipeCategory,
    RecipeThumbSrc,
    RecipeVideoSrc,
)
from users.models import ExceptIngreList, UserIngreList, UserLevel, User
from base.models import RecipeCategoryDict


class RecipePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100

class AllRecipesView(APIView):
    def get(self, request):
        """
        전체 레시피를 JSON 형태로 페이지네이션하여 반환.
        """
        paginator = RecipePagination()
        
        # Query Parameter 처리
        recipe_category = request.query_params.get("recipe_category", None)
        try:
            recipe_category = int(recipe_category) if recipe_category is not None else -1
        except ValueError:
            return Response({"error": "Invalid recipe_category parameter. Must be an integer."}, status=400)

        # QuerySet 구성
        queryset = Recipe.objects.prefetch_related(
            Prefetch("recipeingrelist_set"),  # RecipeIngreList
            Prefetch("recipemainingre_set"),  # RecipeMainIngre
            Prefetch("recipeprogress_set"),  # RecipeProgress
            Prefetch("recipecategory_set"),  # RecipeCategory
        ).select_related(
            "recipethumbsrc",  # Thumbnail
            "recipevideosrc",  # Video source
            "recipetime",      # RecipeTime
        )

        # 카테고리 필터링 (recipe_category == -1이면 필터링 생략)
        if recipe_category != -1:
            queryset = queryset.filter(
                recipecategory__recipe_category__recipe_category_id=recipe_category
            )

        # 페이지네이션 및 결과 반환
        page = paginator.paginate_queryset(queryset, request)
        results = {}

        for recipe in page:
            ingredients = recipe.recipeingrelist_set.all()
            main_ingredients = recipe.recipemainingre_set.all()
            progress = recipe.recipeprogress_set.all()
            categories = recipe.recipecategory_set.all()

            results[recipe.recipe_id] = {
                "recipe_name": recipe.recipe_name,
                "recipe_amount": recipe.recipeamount.recipe_amount,
                "recipe_level": recipe.recipelevel.recipe_level,
                "recipe_time": recipe.recipetime.recipe_time,  # 추가된 조리시간
                "ingredients_title_lst": [i.ingre.ingre_name for i in ingredients],
                "main_ingre": [m.main_ingre.ingre_name for m in main_ingredients],
                "ingredients_amount_lst": [i.ingredients_amount_lst for i in ingredients],
                "recipe_category": [c.recipe_category.recipe_category_name for c in categories],  # 카테고리 이름 반환
                "video_src": recipe.recipevideosrc.video_src if hasattr(recipe, "recipevideosrc") else None,
                "thumb": recipe.recipethumbsrc.thumb_src if hasattr(recipe, "recipethumbsrc") else None,
                "recipe_progress_lst": [p.recipe_progress for p in progress],
                "recipe_progress_img_lst": [p.recipe_img_src for p in progress],
            }

        return paginator.get_paginated_response(results)

##### Filtering API #####
class FilteredRecipesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        recipe_category = int(request.query_params.get("recipe_category", -1))
        paginator = RecipePagination()

        # Step 1: 제외 재료 필터링
        exclude_ingredients = ExceptIngreList.objects.filter(user=user).values_list("ingre__ingre_name", flat=True)
        filtered_queryset = Recipe.objects.exclude(
            recipeingrelist__ingre__ingre_name__in=exclude_ingredients
        )

        # Step 2: 보유 재료 기반 필터링 및 매칭률 계산
        user_ingredients = UserIngreList.objects.filter(user=user).values_list("ingre__ingre_name", flat=True)
        user_priorities = UserIngreList.objects.filter(user=user)

        filtered_queryset = filtered_queryset.annotate(
            match_count=Count("recipeingrelist__ingre__ingre_name", filter=Q(recipeingrelist__ingre__ingre_name__in=user_ingredients)),
            total_count=Count("recipeingrelist__ingre__ingre_name"),
            match_rate=ExpressionWrapper(F("match_count") * 100.0 / F("total_count"), output_field=FloatField())
        ).filter(match_rate__gt=0)

        # Step 3: 주재료 매칭률 및 priority_sum 계산
        priority_subquery = Subquery(
            user_priorities.filter(ingre=OuterRef("recipemainingre__main_ingre")).values("priority")[:1]
        )

        filtered_queryset = filtered_queryset.annotate(
            main_match_count=Count("recipemainingre__main_ingre__ingre_name", filter=Q(recipemainingre__main_ingre__ingre_name__in=user_ingredients)),
            main_total_count=Count("recipemainingre__main_ingre__ingre_name"),
            main_match_rate=ExpressionWrapper(
                F("main_match_count") * 100.0 / F("main_total_count"),
                output_field=FloatField()
            ),
            priority_sum=Sum(priority_subquery, output_field=FloatField())
        )

        # Step 4: 레벨 기반 필터링
        user_level = UserLevel.objects.filter(user=user).first()
        if user_level:
            filtered_queryset = filtered_queryset.filter(
                recipelevel__recipe_level__lte=user_level.user_level
            )

        # Step 5: 카테고리 필터링
        if recipe_category != -1:
            filtered_queryset = filtered_queryset.filter(
                recipecategory__recipe_category__recipe_category_id=recipe_category
            )

        # Step 6: 정렬
        convenience = getattr(user, "convenience", False)
        if convenience:
            filtered_queryset = filtered_queryset.order_by(
                "-main_match_rate", "-match_rate", "-priority_sum", "recipetime__recipe_time"
            )
        else:
            filtered_queryset = filtered_queryset.order_by("-main_match_rate", "-match_rate", "-priority_sum")

        # JSON 응답 구성
        page = paginator.paginate_queryset(filtered_queryset, request)
        results = {}
        for recipe in page:
            results[recipe.recipe_id] = {
                "recipe_name": recipe.recipe_name,
                "recipe_amount": getattr(recipe.recipeamount, "recipe_amount", None),
                "recipe_level": getattr(recipe.recipelevel, "recipe_level", None),
                "recipe_time": getattr(recipe.recipetime, "recipe_time", None),
                "ingredients_title_lst": list(recipe.recipeingrelist_set.values_list("ingre__ingre_name", flat=True)),
                "main_ingre": list(recipe.recipemainingre_set.values_list("main_ingre__ingre_name", flat=True)),
                "ingredients_amount_lst": list(recipe.recipeingrelist_set.values_list("ingredients_amount_lst", flat=True)),
                "recipe_category": list(recipe.recipecategory_set.values_list("recipe_category__recipe_category_name", flat=True)),
                "video_src": getattr(recipe.recipevideosrc, "video_src", None),
                "thumb": getattr(recipe.recipethumbsrc, "thumb_src", None),
                "recipe_progress_lst": list(recipe.recipeprogress_set.values_list("recipe_progress", flat=True)),
                "recipe_progress_img_lst": list(recipe.recipeprogress_set.values_list("recipe_img_src", flat=True)),
                "match_rate": recipe.match_rate,
                "main_match_rate": recipe.main_match_rate,
                "priority_sum": recipe.priority_sum,
            }

        return paginator.get_paginated_response({"results": results})
