### in admin.py ###

from django.contrib import admin
from .models import (
    Recipe,
    RecipeIngreList,
    RecipeMainIngre,
    RecipeCategory,
    RecipeLevel,
    RecipeAmount,
    RecipeTime,
    RecipeVideoSrc,
    RecipeThumbSrc,
    RecipeProgress,
)

# Recipe Admin
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe_id', 'recipe_name')  # 표시할 필드
    search_fields = ('recipe_name',)  # 검색 필드

# Recipe Ingredient List Admin
@admin.register(RecipeIngreList)
class RecipeIngreListAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingre', 'ingredients_amount_lst')  # 표시할 필드
    search_fields = ('recipe__recipe_name', 'ingre__ingre_name')  # 검색 필드
    list_filter = ('recipe',)  # 필터 추가

# Recipe Main Ingredient Admin
@admin.register(RecipeMainIngre)
class RecipeMainIngreAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'main_ingre')
    search_fields = ('recipe__recipe_name', 'main_ingre__ingre_name')
    list_filter = ('recipe',)

# Recipe Category Admin
@admin.register(RecipeCategory)
class RecipeCategoryAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'recipe_category')
    search_fields = ('recipe__recipe_name', 'recipe_category__category_name')
    list_filter = ('recipe_category',)

# Recipe Level Admin
@admin.register(RecipeLevel)
class RecipeLevelAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'recipe_level')
    list_filter = ('recipe_level',)

# Recipe Amount Admin
@admin.register(RecipeAmount)
class RecipeAmountAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'recipe_amount')

# Recipe Time Admin
@admin.register(RecipeTime)
class RecipeTimeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'recipe_time')

# Recipe Video Src Admin
@admin.register(RecipeVideoSrc)
class RecipeVideoSrcAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'video_src')

# Recipe Thumbnail Src Admin
@admin.register(RecipeThumbSrc)
class RecipeThumbSrcAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'thumb_src')

# Recipe Progress Admin
@admin.register(RecipeProgress)
class RecipeProgressAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'recipe_progress', 'recipe_img_src')
    search_fields = ('recipe__recipe_name', 'recipe_progress')
    list_filter = ('recipe',)
