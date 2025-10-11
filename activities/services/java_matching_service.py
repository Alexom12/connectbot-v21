import logging
import aiohttp
import json
from datetime import datetime
from config.settings import JAVA_SERVICE_URL
from activities.services.redis_service import activity_redis_service

logger = logging.getLogger(__name__)

class JavaMatchingService:
    """Сервис для взаимодействия с Java микросервисом matching алгоритмов"""
    
    def __init__(self):
        self.base_url = JAVA_SERVICE_URL
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def match_coffee_pairs(self, participants):
        """
        Формирование пар для Тайного кофе через Java микросервис
        
        Args:
            participants: список сотрудников для matching
            
        Returns:
            список пар [(employee1, employee2), ...]
        """
        try:
            # Подготавливаем данные для отправки
            participant_data = []
            for employee in participants:
                participant_data.append({
                    'id': employee.id,
                    'name': employee.name,
                    'department': employee.department,
                    'position': employee.position,
                    'interests': [interest.name for interest in employee.interests.all()],
                    'telegram_id': employee.telegram_id,
                    'preferences': getattr(employee, 'preferences', {}),
                })
            
            request_data = {
                'participants': participant_data,
                'algorithm': 'cross_department',
                'optimization': 'high',
                'activity_type': 'coffee'
            }
            
            # Проверяем кэш
            cache_key = f"matching_coffee_{hash(json.dumps(request_data, sort_keys=True))}"
            cached_result = await activity_redis_service.get_cached_activity_data(cache_key)
            
            if cached_result:
                logger.info("✅ Использованы кэшированные результаты matching")
                return self._parse_matching_result(cached_result, participants)
            
            # Отправляем запрос к Java микросервису
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/matching/coffee/pairs"
                
                async with session.post(url, json=request_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Кэшируем результат на 1 час
                        await activity_redis_service.cache_activity_data(
                            cache_key, result, timeout=3600
                        )
                        
                        pairs = self._parse_matching_result(result, participants)
                        logger.info(f"✅ Java микросервис вернул {len(pairs)} пар")
                        return pairs
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка Java микросервиса: {response.status} - {error_text}")
                        return self._fallback_matching(participants)
                        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения с Java микросервисом: {e}")
            return self._fallback_matching(participants)
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка в matching: {e}")
            return self._fallback_matching(participants)
    
    async def match_tournament_bracket(self, participants, game_type="chess", format="swiss"):
        """
        Формирование турнирной сетки
        
        Args:
            participants: список участников
            game_type: тип игры (chess, ping_pong)
            format: формат турнира (swiss, round_robin)
        """
        try:
            participant_data = []
            for employee in participants:
                participant_data.append({
                    'id': employee.id,
                    'name': employee.name,
                    'department': employee.department,
                    'rating': getattr(employee, f'{game_type}_rating', 1200),
                    'games_played': getattr(employee, f'{game_type}_games_played', 0),
                })
            
            request_data = {
                'participants': participant_data,
                'game_type': game_type,
                'format': format,
                'rounds': 3 if len(participants) <= 8 else 5
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/matching/tournament/bracket"
                
                async with session.post(url, json=request_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Турнирная сетка создана: {len(result.get('matches', []))} матчей")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка создания турнирной сетки: {error_text}")
                        return self._fallback_tournament(participants, game_type)
                        
        except Exception as e:
            logger.error(f"❌ Ошибка создания турнира: {e}")
            return self._fallback_tournament(participants, game_type)
    
    async def generate_teams(self, participants, team_size=4, balance_skills=True):
        """
        Генерация команд для групповых активностей
        
        Args:
            participants: список участников
            team_size: размер команды
            balance_skills: балансировка по навыкам
        """
        try:
            participant_data = []
            for employee in participants:
                participant_data.append({
                    'id': employee.id,
                    'name': employee.name,
                    'department': employee.department,
                    'skills': {
                        'communication': getattr(employee, 'communication_skill', 3),
                        'creativity': getattr(employee, 'creativity_skill', 3),
                        'leadership': getattr(employee, 'leadership_skill', 3),
                    },
                    'interests': [interest.name for interest in employee.interests.all()],
                })
            
            request_data = {
                'participants': participant_data,
                'team_size': team_size,
                'balance_skills': balance_skills,
                'max_teams': len(participants) // team_size
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/matching/teams/generate"
                
                async with session.post(url, json=request_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Сгенерировано {len(result.get('teams', []))} команд")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка генерации команд: {error_text}")
                        return self._fallback_teams(participants, team_size)
                        
        except Exception as e:
            logger.error(f"❌ Ошибка генерации команд: {e}")
            return self._fallback_teams(participants, team_size)
    
    def _parse_matching_result(self, result, participants):
        """Парсинг результата от Java микросервиса"""
        pairs = []
        participant_dict = {emp.id: emp for emp in participants}
        
        for pair_data in result.get('pairs', []):
            emp1_id = pair_data.get('employee1_id')
            emp2_id = pair_data.get('employee2_id')
            
            if emp1_id in participant_dict and emp2_id in participant_dict:
                pairs.append((
                    participant_dict[emp1_id],
                    participant_dict[emp2_id]
                ))
        
        return pairs
    
    def _fallback_matching(self, participants):
        """Fallback алгоритм matching при недоступности Java сервиса"""
        logger.warning("🔄 Используется fallback matching алгоритм")
        
        # Простой алгоритм - чередование отделов
        departments = {}
        for emp in participants:
            if emp.department not in departments:
                departments[emp.department] = []
            departments[emp.department].append(emp)
        
        pairs = []
        remaining = participants.copy()
        
        while len(remaining) >= 2:
            emp1 = remaining[0]
            
            # Ищем сотрудника из другого отдела
            emp2 = None
            for emp in remaining[1:]:
                if emp.department != emp1.department:
                    emp2 = emp
                    break
            
            # Если не нашли из другого отдела, берем любого
            if not emp2 and len(remaining) >= 2:
                emp2 = remaining[1]
            
            if emp2:
                pairs.append((emp1, emp2))
                remaining.remove(emp1)
                remaining.remove(emp2)
            else:
                break
        
        return pairs
    
    def _fallback_tournament(self, participants, game_type):
        """Fallback создание турнирной сетки"""
        matches = []
        for i in range(0, len(participants)-1, 2):
            if i+1 < len(participants):
                matches.append({
                    'player1_id': participants[i].id,
                    'player2_id': participants[i+1].id,
                    'round': 1,
                    'match_number': i // 2 + 1
                })
        
        return {'matches': matches, 'format': 'fallback_swiss'}
    
    def _fallback_teams(self, participants, team_size):
        """Fallback генерация команд"""
        teams = []
        current_team = []
        
        for emp in participants:
            current_team.append(emp.id)
            if len(current_team) == team_size:
                teams.append({'members': current_team.copy()})
                current_team = []
        
        if current_team:
            teams.append({'members': current_team})
        
        return {'teams': teams}

# Создаем экземпляр сервиса
java_matching_service = JavaMatchingService()