from django.core.management.base import BaseCommand
from activities.services import ActivityManager
import asyncio

class Command(BaseCommand):
    help = 'Создание недельных сессий активностей'

    def handle(self, *args, **options):
        self.stdout.write('Создание недельных сессий активностей...')
        
        async def setup():
            manager = ActivityManager()
            success = await manager.create_weekly_sessions()
            return success
        
        success = asyncio.run(setup())
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Недельные сессии активностей созданы успешно!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Ошибка создания недельных сессий')
            )