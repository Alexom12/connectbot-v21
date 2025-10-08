from django.core.management.base import BaseCommand
from employees.models import Interest, Department, BusinessCenter, Achievement


class Command(BaseCommand):
    help = 'Заполнение начальных данных для ConnectBot'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Заполнение начальных данных...')
        
        self.create_interests()
        self.create_departments() 
        self.create_business_centers()
        self.create_achievements()
        
        self.stdout.write(self.style.SUCCESS('✅ Начальные данные успешно созданы!'))

    def create_interests(self):
        """Создание интересов/активностей"""
        interests_data = [
            {'code': 'coffee', 'name': 'Тайный кофе', 'emoji': '☕️', 'description': 'Еженедельное случайное знакомство двух сотрудников'},
            {'code': 'lunch', 'name': 'Обед вслепую', 'emoji': '🍝', 'description': 'Случайное формирование пар для совместного обеда'},
            {'code': 'walk', 'name': 'Слепая прогулка', 'emoji': '🚶', 'description': '30-минутная прогулка вдвоем с запретом на рабочие темы'},
            {'code': 'chess', 'name': 'Шахматы', 'emoji': '♟️', 'description': 'Быстрые партии и турниры по шахматам'},
            {'code': 'pingpong', 'name': 'Настольный теннис', 'emoji': '🏓', 'description': 'Организация игр в пинг-понг'},
            {'code': 'games', 'name': 'Настольные игры', 'emoji': '🎲', 'description': 'Сбор команд для настольных игр'},
            {'code': 'photo', 'name': 'Фотоквесты', 'emoji': '📸', 'description': 'Командное соревнование по выполнению креативных заданий'},
            {'code': 'masterclass', 'name': 'Мастер-классы', 'emoji': '🧠', 'description': 'Сессии, где сотрудники делятся своими навыками'},
            {'code': 'clubs', 'name': 'Клубы по интересам', 'emoji': '📚', 'description': 'Автоматическое создание чатов для людей со схожими хобби'},
        ]
        
        for interest_data in interests_data:
            interest, created = Interest.objects.get_or_create(
                code=interest_data['code'],
                defaults=interest_data
            )
            if created:
                self.stdout.write(f"✅ Создан интерес: {interest.emoji} {interest.name}")
            else:
                self.stdout.write(f"📝 Обновлен интерес: {interest.emoji} {interest.name}")

    def create_departments(self):
        """Создание отделов"""
        departments = [
            {'name': 'IT отдел', 'code': 'IT'},
            {'name': 'Отдел маркетинга', 'code': 'MARKETING'},
            {'name': 'Отдел продаж', 'code': 'SALES'},
            {'name': 'Бухгалтерия', 'code': 'ACCOUNTING'},
            {'name': 'HR отдел', 'code': 'HR'},
            {'name': 'Отдел разработки', 'code': 'DEVELOPMENT'},
            {'name': 'Техническая поддержка', 'code': 'SUPPORT'},
        ]
        
        for dept_data in departments:
            department, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f"✅ Создан отдел: {department.name}")

    def create_business_centers(self):
        """Создание бизнес-центров"""
        business_centers = [
            {'name': 'БЦ Москва-Сити', 'address': 'Пресненская наб., 8с1'},
            {'name': 'БЦ Око', 'address': '1-й Красногвардейский пр., 21'},
            {'name': 'БЦ Федерация', 'address': 'Пресненская наб., 12'},
            {'name': 'БЦ Гринвич', 'address': 'ул. 8 Марта, 1'},
        ]
        
        for bc_data in business_centers:
            bc, created = BusinessCenter.objects.get_or_create(
                name=bc_data['name'],
                defaults=bc_data
            )
            if created:
                self.stdout.write(f"✅ Создан БЦ: {bc.name}")

    def create_achievements(self):
        """Создание достижений"""
        achievements_data = [
            {
                'name': 'Первая встреча',
                'description': 'Принять участие в первой активности',
                'achievement_type': 'participation',
                'icon': '🎯',
                'condition_type': 'count',
                'condition_value': 1,
                'points_reward': 10,
            },
            {
                'name': 'Социальная бабочка', 
                'description': 'Поучаствовать в 5 разных активностях',
                'achievement_type': 'variety',
                'icon': '🦋',
                'condition_type': 'variety',
                'condition_value': 5,
                'points_reward': 50,
            },
            {
                'name': 'Кофеман',
                'description': 'Принять участие в 3 Тайных кофе',
                'achievement_type': 'consistency',
                'icon': '☕️',
                'condition_type': 'count',
                'condition_value': 3,
                'condition_activity_type': 'coffee',
                'points_reward': 30,
            },
            {
                'name': 'Шахматный гроссмейстер',
                'description': 'Сыграть 10 партий в шахматы',
                'achievement_type': 'expert',
                'icon': '♟️',
                'condition_type': 'count', 
                'condition_value': 10,
                'condition_activity_type': 'chess',
                'points_reward': 100,
            },
        ]
        
        for achievement_data in achievements_data:
            achievement, created = Achievement.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )
            if created:
                self.stdout.write(f"✅ Создано достижение: {achievement.icon} {achievement.name}")