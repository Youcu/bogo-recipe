### in admin.py ###

from django.contrib import admin
from .models import IngreList, IngreLocDict, RecipeCategoryDict

# Ingredients Mapping Table Admin
@admin.register(IngreList)
class IngreListAdmin(admin.ModelAdmin):
    list_display = ('ingre_id', 'ingre_name')  # 표시할 필드
    search_fields = ('ingre_name',)  # 검색 필드

# Ingredient Location Dictionary Admin
@admin.register(IngreLocDict)
class IngreLocDictAdmin(admin.ModelAdmin):
    list_display = ('ingre_loc_id', 'loc_name')  # 표시할 필드
    search_fields = ('loc_name',)  # 검색 필드

# Recipe Category Dictionary Admin
@admin.register(RecipeCategoryDict)
class RecipeCategoryDictAdmin(admin.ModelAdmin):
    list_display = ('recipe_category_id', 'recipe_category_name')  # 표시할 필드
    search_fields = ('recipe_category_name',)  # 검색 필드
