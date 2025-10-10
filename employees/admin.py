from django.contrib import admin
from .models import (
    Employee, Interest, EmployeeInterest, Department, BusinessCenter,
    Activity, ActivityParticipant, Achievement, EmployeeAchievement, BotAdmin,
    SecretCoffee, CoffeePair
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


# === Система "Тайный кофе" ===

class CoffeePairInline(admin.TabularInline):
    """Inline для отображения пар в админке сессий"""
    model = CoffeePair
    extra = 0
    readonly_fields = ['created_at', 'match_score']
    fields = [
        'employee1', 'employee2', 'status', 'match_score',
        'confirmed_employee1', 'confirmed_employee2', 'chat_created'
    ]


@admin.register(SecretCoffee)
class SecretCoffeeAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'week_start', 'status', 'get_pairs_count', 
        'get_confirmed_pairs_count', 'get_participation_rate', 'created_at'
    ]
    list_filter = ['status', 'week_start', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = [
        'created_at', 'updated_at', 'total_participants', 
        'successful_pairs', 'get_pairs_count', 'get_confirmed_pairs_count'
    ]
    inlines = [CoffeePairInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'week_start', 'description', 'status')
        }),
        ('Настройки', {
            'fields': ('max_pairs', 'algorithm_used', 'registration_deadline', 'meeting_deadline')
        }),
        ('Статистика', {
            'fields': ('total_participants', 'successful_pairs', 'get_pairs_count', 'get_confirmed_pairs_count'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_pairs_count(self, obj):
        return obj.get_pairs_count()
    get_pairs_count.short_description = 'Всего пар'
    
    def get_confirmed_pairs_count(self, obj):
        return obj.get_confirmed_pairs_count()
    get_confirmed_pairs_count.short_description = 'Подтвержденных'
    
    def get_participation_rate(self, obj):
        return f"{obj.get_participation_rate()}%"
    get_participation_rate.short_description = 'Участие'


@admin.register(CoffeePair)
class CoffeePairAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'secret_coffee', 'status', 'match_score',
        'confirmed_employee1', 'confirmed_employee2', 'chat_created',
        'meeting_completed', 'created_at'
    ]
    list_filter = [
        'status', 'confirmed_employee1', 'confirmed_employee2', 
        'chat_created', 'meeting_completed', 'secret_coffee__week_start'
    ]
    search_fields = [
        'employee1__full_name', 'employee2__full_name', 
        'secret_coffee__title', 'meeting_place'
    ]
    readonly_fields = [
        'created_at', 'notified_at', 'confirmed_at', 'completed_at', 
        'get_average_rating'
    ]
    
    fieldsets = (
        ('Участники', {
            'fields': ('secret_coffee', 'employee1', 'employee2', 'status')
        }),
        ('Подтверждения', {
            'fields': ('confirmed_employee1', 'confirmed_employee2', 'confirmed_at')
        }),
        ('Чат и встреча', {
            'fields': (
                'chat_created', 'chat_id', 'meeting_scheduled', 
                'meeting_date', 'meeting_place', 'meeting_completed'
            )
        }),
        ('Алгоритм matching', {
            'fields': ('match_score', 'match_reason'),
            'classes': ('collapse',)
        }),
        ('Обратная связь', {
            'fields': (
                'feedback_employee1', 'rating_employee1',
                'feedback_employee2', 'rating_employee2', 'get_average_rating'
            ),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'notified_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_average_rating(self, obj):
        avg = obj.get_average_rating()
        return f"{avg:.1f}" if avg else "Нет оценок"
    get_average_rating.short_description = 'Средняя оценка'