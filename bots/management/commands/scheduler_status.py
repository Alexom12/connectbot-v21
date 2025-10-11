from django.core.management.base import BaseCommand
from bots.services.scheduler_service import scheduler_service

class Command(BaseCommand):
    help = 'Статус планировщика задач ConnectBot'

    def handle(self, *args, **options):
        status = scheduler_service.get_scheduler_status()
        
        self.stdout.write(f"📊 Статус планировщика: {status['status'].upper()}")
        self.stdout.write(f"📅 Количество задач: {status['job_count']}")
        
        if status['jobs']:
            self.stdout.write("\n🎯 Настроенные задачи:")
            for job in status['jobs']:
                self.stdout.write(f"   • {job['name']}")
                self.stdout.write(f"     ID: {job['id']}")
                self.stdout.write(f"     Следующий запуск: {job['next_run']}")
                self.stdout.write(f"     Триггер: {job['trigger']}")
                self.stdout.write("")