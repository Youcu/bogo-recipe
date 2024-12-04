from django.db import models
from base.models import IngreList
from base.models import RecipeCategoryDict

# Recipe Model Definition
class Recipe(models.Model):
    recipe_id = models.AutoField(primary_key=True)  # Recipe 모델의 recipe_id를 PK로 설정
    recipe_name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f"Recipe: {self.recipe_name}"

# Recipe Ingredient List Model Definition
class RecipeIngreList(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)
    ingredients_amount_lst = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingre'], name='unique_recipe_ingre')
        ]

    def __str__(self):
        return f"Recipe: {self.recipe}, Ingredient: {self.ingre}, Amount: {self.ingredients_amount_lst}"

# Recipe Main Ingredient
class RecipeMainIngre(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조
    main_ingre = models.ForeignKey(IngreList, on_delete=models.CASCADE)  # IngreList 모델의 ingre_id를 참조

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "main_ingre"],
                name="unique_recipe_main_ingre"  # recipe와 ingre의 고유 조합 보장
            )
        ]

    def __str__(self):
        return f"Recipe: {self.recipe}, Main Ingredient: {self.main_ingre}"
    
# Recipe Category -> 면, 밥류
class RecipeCategory(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 외래 키
    recipe_category = models.ForeignKey(RecipeCategoryDict, on_delete=models.CASCADE)  # RecipeCategoryDict 모델의 recipe_category_id를 참조하는 외래 키

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'recipe_category'], name='unique_recipe_category')
        ]

    def __str__(self):
        return f"Recipe: {self.recipe}, Category: {self.recipe_category}"
    
# Recipe Level
class RecipeLevel(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 1:1 외래 키
    recipe_level = models.IntegerField(null=False)  # 레시피 난이도 (0: 쉬움, 1: 보통, 2: 어려움 등)

    def __str__(self):
        return f"Recipe: {self.recipe}, Level: {self.recipe_level}"
    
# Recipe Amount (N인분)
class RecipeAmount(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 1:1 외래 키
    recipe_amount = models.IntegerField(null=False)  # 레시피 당 하나의 값만 가짐

    def __str__(self):
        return f"Recipe: {self.recipe}, Amount: {self.recipe_amount}"

# Recipe Time
class RecipeTime(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 1:1 외래 키
    recipe_time = models.IntegerField(null=False)  # 레시피 조리 시간 (분 단위)

    def __str__(self):
        return f"Recipe: {self.recipe}, Time: {self.recipe_time} minutes"
    
# Recipe Video Src
class RecipeVideoSrc(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 1:1 외래 키
    video_src = models.CharField(max_length=255, null=True, blank=True)  # 레시피 동영상 소스 URL

    def __str__(self):
        return f"Recipe: {self.recipe}, Video Src: {self.video_src}"

# Recipe Thumbnail Src
class RecipeThumbSrc(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 1:1 외래 키
    thumb_src = models.CharField(max_length=255, null=False)  # 썸네일 이미지 소스 URL

    def __str__(self):
        return f"Recipe: {self.recipe}, Thumbnail Src: {self.thumb_src}"
    
# Recipe Progress
class RecipeProgress(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)  # Recipe 모델의 recipe_id를 참조하는 외래 키
    recipe_progress = models.CharField(max_length=255, null=False)  # 조리 단계 정보 (예: step1, step2 등)
    recipe_img_src = models.CharField(max_length=255, null=False)  # 해당 조리 단계의 이미지 경로

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "recipe_progress"], name="unique_recipe_progress"
            ),
            models.UniqueConstraint(
                fields=["recipe", "recipe_img_src"], name="unique_recipe_img_src_per_recipe"
            ),
        ]

    def __str__(self):
        return f"Recipe: {self.recipe}, Progress: {self.recipe_progress}, Image Src: {self.recipe_img_src}"



















