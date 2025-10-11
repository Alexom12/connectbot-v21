import logging
import random
import string
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from activities.models import (
    SecretCoffeeMeeting, SecretCoffeePreference, 
    SecretCoffeeMessage, SecretCoffeeProposal,
    ActivitySession, ActivityParticipant
)
from employees.models import Employee
from .java_matching_service import java_matching_service
from activities.services.redis_service import activity_redis_service

logger = logging.getLogger(__name__)

class AnonymousCoffeeService:
    """Сервис для полностью анонимного Тайного кофе"""
    
    def __init__(self):
        self.negotiation_rules = {
            'max_proposals': 3,
            'timeout_minutes': 1440,  # 24 часа
            'auto_confirm': True,
        }
    
    async def run_weekly_matching(self):
        """Запуск еженедельного matching с полной анонимностью"""
        try:
            logger.info("Запуск анонимного matching Тайного кофе...")
            
            # Получаем текущую сессию
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            session = await ActivitySession.objects.select_related().aget(
                activity_type='secret_coffee',
                week_start=week_start
            )
            
            # Получаем участников с предпочтениями
            participants = await self._get_participants_with_preferences(session)
            
            if len(participants) < 2:
                logger.warning("Недостаточно участников для matching")
                return False
            
            # Matching через Java микросервис
            # Извлекаем только объекты Employee для сервиса
            employee_list = [p['employee'] for p in participants]
            pairs = await java_matching_service.match_coffee_pairs(employee_list)
            
            # Преобразуем обратно в формат с предпочтениями
            participant_dict = {p['employee'].id: p for p in participants}
            enhanced_pairs = []
            for emp1, emp2 in pairs:
                enhanced_pairs.append((participant_dict[emp1.id], participant_dict[emp2.id]))
            pairs = enhanced_pairs
            
            if not pairs:
                logger.error("Не удалось сформировать пары")
                return False
            
            # Создаем анонимные встречи
            created_meetings = await self._create_anonymous_meetings(session, pairs)
            
            # Отправляем начальные уведомления
            await self._send_initial_notifications(created_meetings)
            
            session.status = 'active'
            await session.asave()
            
            logger.info(f"Создано {len(created_meetings)} анонимных встреч")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка в анонимном matching: {e}")
            return False
    
    async def _get_participants_with_preferences(self, session):
        """Получить участников с их предпочтениями"""
        participants_qs = ActivityParticipant.objects.filter(
            activity_session=session,
            subscription_status=True
        ).select_related('employee')
        
        participants = []
        async for participant in participants_qs:
            try:
                # Получаем предпочтения сотрудника
                preferences = await SecretCoffeePreference.objects.aget(
                    employee=participant.employee
                )
                participants.append({
                    'employee': participant.employee,
                    'preferences': preferences
                })
            except SecretCoffeePreference.DoesNotExist:
                logger.warning(f"У сотрудника {participant.employee.full_name} нет предпочтений")
                # Создаем дефолтные предпочтения
                preferences = await SecretCoffeePreference.objects.acreate(
                    employee=participant.employee,
                    availability_slots=['mon_10-12', 'tue_14-16', 'wed_12-14', 'thu_16-18', 'fri_11-13'],
                    preferred_format='BOTH',
                    topics_of_interest=['работа', 'хобби', 'путешествия', 'технологии']
                )
                participants.append({
                    'employee': participant.employee,
                    'preferences': preferences
                })
        
        return participants
    
    async def _create_anonymous_meetings(self, session, pairs):
        """Создание анонимных встреч с кодами и знаками"""
        meetings = []
        
        for emp1_data, emp2_data in pairs:
            emp1 = emp1_data['employee']
            emp2 = emp2_data['employee']
            
            # Генерируем уникальные коды
            meeting_id = self._generate_meeting_id()
            emp1_code = self._generate_employee_code()
            emp2_code = self._generate_employee_code()
            recognition_sign = self._generate_recognition_sign()
            
            # Определяем формат встречи на основе предпочтений
            meeting_format = self._determine_meeting_format(
                emp1_data['preferences'], 
                emp2_data['preferences']
            )
            
            meeting = await SecretCoffeeMeeting.objects.acreate(
                meeting_id=meeting_id,
                activity_session=session,
                employee1=emp1,
                employee2=emp2,
                employee1_code=emp1_code,
                employee2_code=emp2_code,
                recognition_sign=recognition_sign,
                meeting_format=meeting_format,
                status='scheduling'
            )
            
            meetings.append(meeting)
            
            logger.info(f"Создана анонимная встреча {meeting_id}")
        
        return meetings
    
    async def _send_initial_notifications(self, meetings):
        """Отправка начальных уведомлений участникам"""
        from bots.handlers.notification_handlers import send_telegram_message
        
        for meeting in meetings:
            # Уведомление для employee1
            message1 = f"""🎭 *ТАЙНЫЙ КОФЕ НАЗНАЧЕН!*

🤫 Сохраняйте тайну! Личность партнера откроется только при встрече.

💬 Начните планирование через бота-посредника:
/schedule_meeting_{meeting.meeting_id}

📋 Ваш код: `{meeting.employee1_code}`
🎯 Система: полностью анонимная

⚡️ Начните диалог первым!"""
            
            # Уведомление для employee2
            message2 = f"""🎭 *ТАЙНЫЙ КОФЕ НАЗНАЧЕН!*

🤫 Сохраняйте тайну! Личность партнера откроется только при встрече.

💬 Ожидайте инициативы партнера для планирования встречи.

📋 Ваш код: `{meeting.employee2_code}`
🎯 Система: полностью анонимная

⏳ Бот уведомит о предложении встречи!"""
            
            await send_telegram_message(meeting.employee1.telegram_id, message1)
            await send_telegram_message(meeting.employee2.telegram_id, message2)
    
    async def handle_meeting_scheduling(self, meeting_id, employee):
        """Обработка начала планирования встречи"""
        try:
            meeting = await SecretCoffeeMeeting.objects.select_related(
                'employee1', 'employee2'
            ).aget(meeting_id=meeting_id)
            
            # Проверяем, что сотрудник является участником встречи
            if employee not in [meeting.employee1, meeting.employee2]:
                return False, "❌ Вы не участник этой встречи"
            
            # Определяем, кто является партнером
            partner = meeting.employee2 if employee == meeting.employee1 else meeting.employee1
            employee_code = meeting.employee1_code if employee == meeting.employee1 else meeting.employee2_code
            
            return True, {
                'meeting': meeting,
                'partner': partner,
                'employee_code': employee_code,
                'recognition_sign': meeting.recognition_sign
            }
            
        except SecretCoffeeMeeting.DoesNotExist:
            return False, "❌ Встреча не найдена"
    
    async def send_message_via_bot(self, meeting, from_employee, message_text):
        """Отправка сообщения через бота-посредника"""
        try:
            # Сохраняем сообщение
            message = await SecretCoffeeMessage.objects.acreate(
                meeting=meeting,
                from_employee=from_employee,
                message_type='text',
                content=message_text,
                is_forwarded=False
            )
            
            # Определяем получателя
            to_employee = meeting.employee2 if from_employee == meeting.employee1 else meeting.employee1
            
            # Форматируем сообщение для пересылки
            forwarded_message = f"💬 Ваш партнер пишет:\n\n\"{message_text}\""
            
            from bots.handlers.notification_handlers import send_telegram_message
            await send_telegram_message(to_employee.telegram_id, forwarded_message)
            
            # Помечаем как пересланное
            message.is_forwarded = True
            await message.asave()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False
    
    async def handle_meeting_proposal(self, meeting, from_employee, proposed_date, proposed_location):
        """Обработка предложения встречи"""
        try:
            # Проверяем лимит предложений
            proposals_count = await SecretCoffeeProposal.objects.filter(
                meeting=meeting,
                from_employee=from_employee
            ).acount()
            
            if proposals_count >= self.negotiation_rules['max_proposals']:
                return False, f"❌ Лимит предложений исчерпан (макс. {self.negotiation_rules['max_proposals']})"
            
            # Создаем предложение
            proposal = await SecretCoffeeProposal.objects.acreate(
                meeting=meeting,
                from_employee=from_employee,
                proposed_date=proposed_date,
                proposed_location=proposed_location,
                proposed_format=meeting.meeting_format,
                status='pending'
            )
            
            # Уведомляем партнера
            to_employee = meeting.employee2 if from_employee == meeting.employee1 else meeting.employee1
            
            proposal_text = f"""📅 *ПРЕДЛОЖЕНИЕ ВСТРЕЧИ*

🗓️ Дата: {proposed_date.strftime('%d.%m.%Y %H:%M')}
📍 Место: {proposed_location}
💻 Формат: {meeting.meeting_format}

✅ Принять: /accept_proposal_{proposal.id}
❌ Отклонить: /reject_proposal_{proposal.id}
💡 Предожить другое: /counter_proposal_{proposal.id}"""
            
            from bots.handlers.notification_handlers import send_telegram_message
            await send_telegram_message(to_employee.telegram_id, proposal_text)
            
            return True, "✅ Предложение отправлено партнеру"
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки предложения: {e}")
            return False, "❌ Ошибка при создании предложения"
    
    async def handle_emergency_stop(self, meeting, employee):
        """Обработка экстренной остановки встречи"""
        try:
            meeting.emergency_stopped = True
            meeting.status = 'cancelled'
            await meeting.asave()
            
            # Уведомляем модератора
            await self._notify_moderator(meeting, employee)
            
            # Уведомляем партнера (без деталей)
            partner = meeting.employee2 if employee == meeting.employee1 else meeting.employee1
            emergency_message = f"""🚨 *ВСТРЕЧА ОТМЕНЕНА*

По техническим причинам встреча отменена.

Приносим извинения за неудобства."""
            
            from bots.handlers.notification_handlers import send_telegram_message
            await send_telegram_message(partner.telegram_id, emergency_message)
            
            return True, "✅ Экстренная остановка выполнена. Модератор уведомлен."
            
        except Exception as e:
            logger.error(f"❌ Ошибка экстренной остановки: {e}")
            return False, "❌ Ошибка при остановке встречи"
    
    def _generate_meeting_id(self):
        """Генерация ID встречи"""
        return f"SC_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    
    def _generate_employee_code(self):
        """Генерация кода сотрудника"""
        adjectives = ['КРАСНЫЙ', 'СИНИЙ', 'ЗЕЛЕНЫЙ', 'ВЕСЕЛЫЙ', 'ТАИНСТВЕННЫЙ', 'СЧАСТЛИВЫЙ']
        nouns = ['СЛОН', 'ТИГР', 'КОТ', 'ДРАКОН', 'ЕДИНОРОГ', 'ФЕНИКС']
        return f"{random.choice(adjectives)}_{random.choice(nouns)}"
    
    def _generate_recognition_sign(self):
        """Генерация опознавательного знака"""
        signs = [
            "КРАСНАЯ РОЗА на столе",
            "КНИГА '1984'",
            "СКАЧКИ ЕДИНОРОГА",
            "СИНИЙ ЗОНТИК",
            "ЖЕЛТЫЙ ШАРФ",
            "ЗЕЛЕНЫЙ ЧАЙНИК"
        ]
        return random.choice(signs)
    
    def _determine_meeting_format(self, pref1, pref2):
        """Определение формата встречи на основе предпочтений"""
        if pref1.preferred_format == 'ONLINE' or pref2.preferred_format == 'ONLINE':
            return 'ONLINE'
        elif pref1.preferred_format == 'OFFLINE' and pref2.preferred_format == 'OFFLINE':
            return 'OFFLINE'
        else:
            return 'ONLINE'  # По умолчанию онлайн для безопасности
    
    async def _notify_moderator(self, meeting, reporting_employee):
        """Уведомление модератора об экстренной ситуации"""
        # TODO: Реализовать уведомление модератора
        logger.warning(f"Экстренная остановка встречи {meeting.meeting_id} от {reporting_employee.full_name}")

# Создаем экземпляр сервиса
anonymous_coffee_service = AnonymousCoffeeService()