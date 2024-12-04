### in users_admin.py ###

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    UserIngreList,
    ExceptIngreList,
    UserLevel,
    Bookmark,
    History,
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Admin에서 표시할 필드 지정
    list_display = ('email', 'name', 'is_active', 'is_staff')  # 'username' 대신 'email' 사용
    list_filter = ('is_active', 'is_staff', 'gender')  # 적절한 필터 필드 추가
    search_fields = ('email', 'name')  # 검색 가능한 필드 설정
    ordering = ('email',)  # 'username' 대신 'email' 기준으로 정렬

    # 필드 구성
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'gender', 'convenience')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'gender', 'convenience'),
        }),
    )

# User Admin
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('email', 'name', 'is_active', 'is_staff', 'gender', 'convenience')  # 표시할 필드
#     search_fields = ('email', 'name')  # 검색 필드
#     list_filter = ('is_active', 'is_staff', 'gender', 'convenience')  # 필터 추가

# User Ingredients List Admin
@admin.register(UserIngreList)
class UserIngreListAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingre', 'user_ingre_amount', 'expiry', 'ingre_loc', 'priority')
    search_fields = ('user__email', 'ingre__ingre_name')
    list_filter = ('ingre_loc', 'expiry')
    actions = ['calculate_priority_action']  # 커스텀 액션

    def calculate_priority_action(self, request, queryset):
        """
        선택된 UserIngreList 항목들의 priority를 재계산합니다.
        """
        for item in queryset:
            item.calculate_priority()
        self.message_user(request, "Priority has been recalculated for the selected items.")
    calculate_priority_action.short_description = "Recalculate priority for selected items"

# Except Ingredients List Admin
@admin.register(ExceptIngreList)
class ExceptIngreListAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingre')
    search_fields = ('user__email', 'ingre__ingre_name')

# User Level Admin
@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_level')
    search_fields = ('user__email',)

# Bookmark Admin
@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__recipe_name')

# History Admin
@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__recipe_name')