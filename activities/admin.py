from django.contrib import admin
from .models import ActivitySession, ActivityParticipant, ActivityPair

@admin.register(ActivitySession)
class ActivitySessionAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'week_start', 'status', 'created_at']
    list_filter = ['activity_type', 'status', 'week_start']
    search_fields = ['activity_type']

@admin.register(ActivityParticipant)
class ActivityParticipantAdmin(admin.ModelAdmin):
    list_display = ['employee', 'activity_session', 'subscription_status', 'joined_at']
    list_filter = ['subscription_status', 'activity_session__activity_type']
    search_fields = ['employee__name', 'employee__telegram_id']

@admin.register(ActivityPair)
class ActivityPairAdmin(admin.ModelAdmin):
    list_display = ['activity_session', 'employee1', 'employee2', 'chat_created', 'created_at']
    list_filter = ['chat_created', 'activity_session__activity_type']
    search_fields = ['employee1__name', 'employee2__name']