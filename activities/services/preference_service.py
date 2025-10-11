import logging
from activities.models import SecretCoffeePreference
from employees.models import Employee

logger = logging.getLogger(__name__)

class PreferenceService:
    """Сервис для управления предпочтениями сотрудников"""
    
    async def get_or_create_preferences(self, employee):
        """Получить или создать предпочтения сотрудника"""
        try:
            preferences, created = await SecretCoffeePreference.objects.aget_or_create(
                employee=employee,
                defaults={
                    'availability_slots': ['mon_10-12', 'tue_14-16', 'wed_12-14', 'thu_16-18', 'fri_11-13'],
                    'preferred_format': 'BOTH',
                    'topics_of_interest': ['работа', 'хобби', 'путешествия', 'технологии'],
                    'office_location': 'MAIN_OFFICE',
                }
            )
            
            if created:
                logger.info(f"✅ Созданы предпочтения для {employee.name}")
            else:
                logger.info(f"✅ Найдены предпочтения для {employee.name}")
                
            return preferences
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения предпочтений: {e}")
            return None
    
    async def update_availability(self, employee, availability_slots):
        """Обновление доступности сотрудника"""
        try:
            preferences = await self.get_or_create_preferences(employee)
            preferences.availability_slots = availability_slots
            await preferences.asave()
            
            logger.info(f"✅ Обновлена доступность для {employee.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления доступности: {e}")
            return False
    
    async def update_format_preference(self, employee, preferred_format):
        """Обновление предпочтительного формата"""
        try:
            preferences = await self.get_or_create_preferences(employee)
            preferences.preferred_format = preferred_format
            await preferences.asave()
            
            logger.info(f"✅ Обновлен формат встреч для {employee.name}: {preferred_format}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления формата: {e}")
            return False
    
    async def update_interests(self, employee, topics_of_interest):
        """Обновление тем для разговора"""
        try:
            preferences = await self.get_or_create_preferences(employee)
            preferences.topics_of_interest = topics_of_interest
            await preferences.asave()
            
            logger.info(f"✅ Обновлены интересы для {employee.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления интересов: {e}")
            return False

# Создаем экземпляр сервиса
preference_service = PreferenceService()