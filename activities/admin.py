from django.contrib import admin
from django.apps import apps

# Import models dynamically to support compatibility aliases
ActivitySession = apps.get_model('activities', 'ActivitySession')
ActivityParticipant = apps.get_model('activities', 'ActivityParticipant')
ActivityPair = apps.get_model('activities', 'ActivityPair')


@admin.register(ActivitySession)
class ActivitySessionAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'week_start', 'status', 'created_at']
    list_filter = ['activity_type', 'status', 'week_start']
    search_fields = ['activity_type']


@admin.register(ActivityParticipant)
class ActivityParticipantAdmin(admin.ModelAdmin):
    """Admin адаптируется под поля модели ActivityParticipant.

    Ранее поля назывались 'activity_session', 'subscription_status' и 'joined_at'.
    В новой модели (employees.ActivityParticipant) поля — 'activity', 'status',
    'invited_at' и т.д. Здесь выбираем отображение в зависимости от наличия полей.
    """
    # Попытка использовать новые имена полей
    try:
        ActivityParticipant._meta.get_field('activity')
        list_display = ['employee', 'activity', 'status', 'invited_at']
        list_filter = ['status', 'activity__activity_type']
        search_fields = ['employee__full_name', 'employee__telegram_id']
    except Exception:
        # Фоллбек на старые имена (если модель — локальная activities.ActivityParticipant)
        list_display = ['employee', 'activity_session', 'subscription_status', 'joined_at']
        list_filter = ['subscription_status', 'activity_session__activity_type']
        search_fields = ['employee__name', 'employee__telegram_id']


@admin.register(ActivityPair)
class ActivityPairAdmin(admin.ModelAdmin):
    list_display = ['activity_session', 'employee1', 'employee2', 'chat_created', 'created_at']
    list_filter = ['chat_created', 'activity_session__activity_type']
    search_fields = ['employee1__full_name', 'employee2__full_name']