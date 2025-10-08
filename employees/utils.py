"""
Утилиты для работы с авторизацией сотрудников
"""
import logging
from asgiref.sync import sync_to_async
from django.conf import settings
from .models import Employee, EmployeeInterest, Interest

logger = logging.getLogger(__name__)


class AuthManager:
    """Менеджер авторизации сотрудников"""
    
    @staticmethod
    @sync_to_async
    def authorize_employee(telegram_user):
        """
        Авторизация сотрудника по данным Telegram
        Возвращает (employee, is_new_authorization)
        """
        try:
            employee = Employee.find_by_telegram_data(telegram_user)
            
            if not employee:
                return None, False
            
            # Обновляем Telegram данные если нужно
            is_updated = employee.update_telegram_data(telegram_user)
            
            # Обновляем статус авторизации
            if not employee.authorized:
                employee.authorized = True
                employee.save(update_fields=['authorized', 'last_activity'])
                return employee, True
            else:
                employee.save(update_fields=['last_activity'])
                return employee, False
                
        except Exception as e:
            logger.error(f"Ошибка авторизации сотрудника: {e}")
            return None, False
    
    @staticmethod
    @sync_to_async 
    def get_unauthorized_message():
        """Сообщение для неавторизованных пользователей"""
        return f"""
🔐 *Доступ к ConnectBot ограничен*

Для использования бота необходимо быть сотрудником компании.

Если вы сотрудник, но не можете войти:

1. Обратитесь к администратору
2. Предоставьте ваш Telegram: @{{username}}

📞 *Контакт администратора:*
@{settings.ADMIN_USERNAME or 'hr_admin'} (Ирина Петрова)

Или напишите на email: {settings.ADMIN_EMAIL or 'hr@company.com'}

После добавления перезапустите бота командой /start
"""
    
    @staticmethod
    @sync_to_async
    def get_welcome_message(employee):
        """Приветственное сообщение для авторизованного сотрудника"""
        interests_count = EmployeeInterest.objects.filter(
            employee=employee, 
            is_active=True
        ).count()
        
        return f"""
🎉 *Добро пожаловать, {employee.full_name.split()[0]}!*

Вы успешно авторизованы в ConnectBot!

📊 *Ваш профиль:*
• Должность: {employee.position or 'Не указана'}
• Отдел: {employee.department.name if employee.department else 'Не указан'}
• БЦ: {employee.business_center.name if employee.business_center else 'Не указан'}

🎯 *Активные подписки:* {interests_count}

Для настройки уведомлений используйте команду /preferences
Главное меню: /menu

Начните общаться с коллегами! 🚀
"""


class PreferenceManager:
    """Менеджер управления предпочтениями"""
    
    @staticmethod
    @sync_to_async
    def get_employee_interests(employee):
        """Получить интересы сотрудника"""
        return list(EmployeeInterest.objects.filter(
            employee=employee
        ).select_related('interest'))
    
    @staticmethod
    @sync_to_async
    def get_all_interests():
        """Получить все доступные интересы"""
        return list(Interest.objects.filter(is_active=True))
    
    @staticmethod
    @sync_to_async
    def update_employee_interests(employee, interest_codes):
        """
        Обновление интересов сотрудника
        """
        try:
            # Получаем все активные интересы
            all_interests = Interest.objects.filter(is_active=True)
            interest_dict = {interest.code: interest for interest in all_interests}
            
            # Получаем текущие интересы сотрудника
            current_interests = EmployeeInterest.objects.filter(employee=employee)
            current_dict = {ei.interest.code: ei for ei in current_interests}
            
            # Обновляем интересы
            for interest_code, interest in interest_dict.items():
                if interest_code in interest_codes:
                    # Активируем интерес
                    if interest_code in current_dict:
                        ei = current_dict[interest_code]
                        if not ei.is_active:
                            ei.is_active = True
                            ei.save()
                    else:
                        EmployeeInterest.objects.create(
                            employee=employee,
                            interest=interest,
                            is_active=True
                        )
                else:
                    # Деактивируем интерес
                    if interest_code in current_dict:
                        ei = current_dict[interest_code]
                        if ei.is_active:
                            ei.is_active = False
                            ei.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления интересов: {e}")
            return False
    
    @staticmethod
    @sync_to_async
    def disable_all_interests(employee):
        """Отписаться от всех интересов"""
        try:
            EmployeeInterest.objects.filter(employee=employee).update(is_active=False)
            return True
        except Exception as e:
            logger.error(f"Ошибка отключения всех интересов: {e}")
            return False