from django.db import models
from base.models import IngreList, IngreLocDict
from datetime import date
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.timezone import now  # 시간 저장용

# Custom UserManager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        이메일을 기반으로 사용자 생성
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        슈퍼유저 생성
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# Custom User Model
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=100)  # 이메일 필드
    name = models.CharField(max_length=100)  # 사용자 이름
    gender = models.CharField(max_length=1, blank=True, null=True)  # 사용자 성별
    convenience = models.BooleanField(default=False)  # 간편식 선호 여부
    is_active = models.BooleanField(default=True)  # 계정 활성화 여부
    is_staff = models.BooleanField(default=False)  # 관리자 여부

    objects = CustomUserManager()  # CustomUserManager 사용

    USERNAME_FIELD = 'email'  # 인증 필드로 이메일 사용
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email


# User's holding ingredients
class UserIngreList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자 모델 참조
    ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)  # 재료 목록 참조
    user_ingre_amount = models.CharField(max_length=20)  # 사용자가 보유한 재료의 양
    expiry = models.DateField(null=False)  # 유통기한
    ingre_loc = models.ForeignKey(IngreLocDict, on_delete=models.SET_NULL, null=True)  # 위치 정보 참조
    priority = models.IntegerField(null=True, blank=True)  # 재료 우선순위 (중복 가능)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'ingre'], name='unique_user_ingre')  # 사용자-재료 조합 고유
        ]

    def calculate_priority(self):
        if self.expiry:
            days_left = (self.expiry - date.today()).days

            # 유통기한에 따른 우선순위 등급 계산
            if days_left <= 0:
                self.priority = 100  # D-Day (유통기한이 오늘이거나 지남)
            elif days_left <= 3:
                self.priority = 90
            elif days_left <= 7:
                self.priority = 70
            elif days_left <= 14:
                self.priority = 50
            elif days_left <= 30:
                self.priority = 30
            else:
                self.priority = 10  # 유통기한이 많이 남아 있음
        else:
            self.priority = 0  # 유통기한이 없거나 알 수 없는 경우 기본값

    def __str__(self):
        return f"User: {self.user}, Ingredient: {self.ingre}, Priority: {self.priority}"

# User's Exception of Ingredients
class ExceptIngreList(models.Model):
    ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)  # IngreList의 ingre_id를 참조하는 외래 키
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User 모델의 user_id를 참조하는 외래 키

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'ingre'], name='unique_except_ingre')  # user와 제외 재료의 조합이 고유해야 함
        ]

    def __str__(self):
        return f"{self.user} 제외 재료: {self.ingre}"


# User Level
class UserLevel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)  # User 모델의 user_id를 참조하는 외래 키
    user_level = models.CharField(max_length=255, null=False)  # 사용자의 레벨

    def __str__(self):
        return f"{self.user} - Level: {self.user_level}"


# # Ingredients' Expiry
# class Expiry(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # User 모델의 user_id를 참조하는 외래 키
#     ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)  # IngreList의 ingre_id를 참조하는 외래 키
#     expiry = models.DateField(null=False)  # 재료의 유통기한

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['user', 'ingre'], name='unique_expiry_ingre')  # user와 ingre의 조합이 고유해야 함
#         ]

#     def __str__(self):
#         return f"User: {self.user}, Ingredient: {self.ingre}, Expiry: {self.expiry}"


# # User's Ingredient Location => 냉장고, 냉동실, 선반
# class IngreLoc(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # User 모델의 user_id를 참조하는 외래 키
#     ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)  # IngreList 모델의 ingre_id를 참조하는 외래 키
#     ingre_loc = models.ForeignKey(IngreLocDict, on_delete=models.CASCADE)  # IngreLocDict 모델의 ingre_loc_id를 참조하는 외래 키

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['user', 'ingre'], name='unique_ingre_loc')  # user와 ingre의 조합이 고유해야 함
#         ]

#     def __str__(self):
#         return f"User: {self.user}, Ingredient: {self.ingre}, Location: {self.ingre_loc}"


# # User Ingredient Priority
# class IngrePriority(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # User 모델의 user_id를 참조하는 외래 키
#     ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)  # IngreList 모델의 ingre_id를 참조하는 외래 키
#     ingre_priority = models.IntegerField(null=False)  # 재료의 우선순위 (정수값)

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['user', 'ingre'], name='unique_ingre_priority')  # user와 ingre의 조합이 고유해야 함
#         ]

#     def calculate_priority(self):
#         # Expiry 모델의 expiry 값을 참조하여 우선순위를 계산
#         try:
#             # user와 ingre 기준으로 Expiry 객체 조회
#             expiry = Expiry.objects.get(user=self.user, ingre=self.ingre)
#             days_left = (expiry.expiry - date.today()).days

#             # 유통기한이 가까울수록 높은 우선순위
#             if days_left == 0:
#                 priority = 100  # D-Day = 0 이면 최우선 사용
#             elif days_left <= 3:
#                 priority = 90
#             elif days_left <= 7:
#                 priority = 70
#             elif days_left <= 14:
#                 priority = 50
#             elif days_left <= 30:
#                 priority = 30
#             else:
#                 priority = 10  # 유통기한이 많이 남아 있는 경우 낮은 우선순위
#         except Expiry.DoesNotExist:
#             # 만약 Expiry 객체가 없을 경우 기본 우선순위 설정
#             priority = 0

#         self.ingre_priority = priority
#         self.save()

#     def __str__(self):
#         return f"User: {self.user}, Ingredient: {self.ingre}, Priority: {self.ingre_priority}"


# Bookmark
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User 모델의 user_id를 참조하는 외래 키
    recipe = models.ForeignKey('recipes.Recipe', on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 외래 키

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'], name='unique_bookmark')  # user와 recipe의 조합이 고유해야 함
        ]

    def __str__(self):
        return f"User: {self.user}, Recipe: {self.recipe}"


# History
class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User 모델의 user_id를 참조하는 외래 키
    recipe = models.ForeignKey('recipes.Recipe', on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 외래 키
    viewed_at = models.DateTimeField(default=now)  # 열람 날짜 저장

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'], name='unique_history')  # user와 recipe의 조합이 고유해야 함
        ]

    def __str__(self):
        return f"User: {self.user}, Recipe: {self.recipe}, Viewed At: {self.viewed_at}"
