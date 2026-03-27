
from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'user__email']
