from django.db import models

# Ingredients Mapping Table
class IngreList(models.Model):
    ingre_id = models.AutoField(primary_key=True)  # Auto Matching PK
    ingre_name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.ingre_name

# 냉장고, 냉동실, 선반
class IngreLocDict(models.Model):
    ingre_loc_id = models.AutoField(primary_key=True)  # Primary Key
    loc_name = models.CharField(max_length=20, null=False)

    def __str__(self):
        return self.loc_name

# Recipe Category -> 밑반찬, 면류, 밥류
class RecipeCategoryDict(models.Model):
    recipe_category_id = models.AutoField(primary_key=True)  # Primary Key
    recipe_category_name = models.CharField(max_length=20, null=False)

    def __str__(self):
        return self.recipe_category_name



