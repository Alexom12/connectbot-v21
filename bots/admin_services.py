# bots/admin_services.py

import logging
from django.utils import timezone
from employees.models import Employee, AdminUser, AdminLog
from activities.models import ActivitySession, ActivityParticipant, SecretCoffeeMeeting
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AdminAuthService:
    """Сервис аутентификации администраторов"""
    
    @staticmethod
    async def is_user_admin(telegram_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        try:
            employee = await Employee.objects.aget(telegram_id=telegram_id)
            admin_user = await AdminUser.objects.select_related('user').aget(user=employee)
            return admin_user.is_active
        except (Employee.DoesNotExist, AdminUser.DoesNotExist):
            return False
    
    @staticmethod
    async def get_admin_user(telegram_id: int) -> Optional[AdminUser]:
        """Получает объект администратора"""
        try:
            employee = await Employee.objects.aget(telegram_id=telegram_id)
            return await AdminUser.objects.select_related('user').aget(user=employee)
        except (Employee.DoesNotExist, AdminUser.DoesNotExist):
            return None


class AdminStatsService:
    """Сервис статистики для админ-панели"""
    
    @staticmethod
    async def get_system_stats() -> Dict:
        """Получает системную статистику"""
        from asgiref.sync import sync_to_async
        
        total_users = await sync_to_async(Employee.objects.count)()
        active_meetings = await sync_to_async(SecretCoffeeMeeting.objects.filter(
            status='active'
        ).count)()
        coffee_sessions = await sync_to_async(ActivitySession.objects.filter(
            activity_type='secret_coffee'
        ).count)()
        
        # Расчет успешности matching (упрощенный)
        total_matches = await sync_to_async(SecretCoffeeMeeting.objects.count)()
        successful_matches = await sync_to_async(SecretCoffeeMeeting.objects.filter(
            status='completed'
        ).count)()
        
        matching_rate = (successful_matches / total_matches * 100) if total_matches > 0 else 0
        
        return {
            'total_users': total_users,
            'active_meetings': active_meetings,
            'coffee_sessions': coffee_sessions,
            'matching_rate': round(matching_rate, 1)
        }


class AdminLogService:
    """Сервис логирования действий администраторов"""
    
    @staticmethod
    async def log_action(
        admin: AdminUser,
        action: str,
        command: str = "",
        target_type: str = "",
        target_id: int = None,
        details: Dict = None
    ):
        """Логирует действие администратора"""
        log_entry = AdminLog(
            admin=admin,
            action=action,
            command=command,
            target_type=target_type,
            target_id=target_id,
            details=details or {}
        )
        await log_entry.asave()
# bots/admin_services.py - ДОБАВЛЯЕМ В КОНЕЦ ФАЙЛА

class SystemHealthService:
    """Сервис проверки здоровья системы"""
    
    @staticmethod
    async def check_system_health() -> Dict:
        """Проверяет здоровье всех компонентов системы"""
        health_checks = {}
        
        try:
            # Проверка базы данных
            from asgiref.sync import sync_to_async
            test_employee = await sync_to_async(Employee.objects.first)()
            health_checks['database'] = {
                'status': 'healthy',
                'details': 'База данных доступна'
            }
        except Exception as e:
            health_checks['database'] = {
                'status': 'unhealthy',
                'details': f'Ошибка БД: {str(e)}'
            }
        
        try:
            # Проверка Redis
            import redis
            from django.conf import settings
            
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            r.ping()
            health_checks['redis'] = {
                'status': 'healthy',
                'details': 'Redis доступен'
            }
        except Exception as e:
            health_checks['redis'] = {
                'status': 'unhealthy',
                'details': f'Ошибка Redis: {str(e)}'
            }
        
        # Определение общего статуса
        all_healthy = all(check['status'] == 'healthy' for check in health_checks.values())
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'components': health_checks,
            'timestamp': timezone.now().isoformat()
        }