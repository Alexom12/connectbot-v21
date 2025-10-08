from django.contrib import admin
from .models import (
    Employee, Interest, EmployeeInterest, Department, BusinessCenter,
    Activity, ActivityParticipant, Achievement, EmployeeAchievement, BotAdmin
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(BusinessCenter)
class BusinessCenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'address']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'position', 'department', 'business_center', 
        'telegram_username', 'authorized', 'is_active'
    ]
    list_filter = ['department', 'business_center', 'authorized', 'is_active']
    search_fields = ['full_name', 'telegram_username', 'position']
    readonly_fields = ['created_at', 'updated_at', 'last_activity']


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'code', 'is_active', 'auto_schedule']
    list_filter = ['is_active', 'auto_schedule']
    search_fields = ['name', 'code']


class EmployeeInterestInline(admin.TabularInline):
    model = EmployeeInterest
    extra = 1
    fields = ['interest', 'is_active', 'receive_notifications']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'activity_type', 'interest', 'scheduled_date', 
        'status', 'max_participants', 'is_auto_created'
    ]
    list_filter = ['activity_type', 'status', 'interest', 'is_auto_created']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'points_reward', 'is_active']
    list_filter = ['achievement_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(BotAdmin)
class BotAdminAdmin(admin.ModelAdmin):
    list_display = ['employee', 'is_super_admin', 'added_at']
    list_filter = ['is_super_admin']
    search_fields = ['employee__full_name']