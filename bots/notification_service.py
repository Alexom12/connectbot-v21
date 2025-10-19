import asyncio
from telegram import Bot
from telegram.error import TelegramError

class NotificationService:
    """
    Сервис для отправки уведомлений пользователям.
    """
    def __init__(self, bot: Bot):
        if not isinstance(bot, Bot):
            raise ValueError("Параметр bot должен быть экземпляром telegram.Bot")
        self.bot = bot

    async def send_notification(self, user_id: int, message: str) -> bool:
        """
        Отправляет текстовое уведомление пользователю.

        :param user_id: ID пользователя в Telegram.
        :param message: Текст сообщения.
        :return: True, если сообщение успешно отправлено, иначе False.
        """
        try:
            await self.bot.send_message(chat_id=user_id, text=message)
            # log.info(f"Уведомление успешно отправлено пользователю {user_id}")
            return True
        except TelegramError as e:
            # log.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
            return False

async def main():
    # Пример использования (для локального тестирования)
    # Замените 'YOUR_TOKEN' и 'USER_ID' на реальные значения
    from config.settings import TELEGRAM_TOKEN
    
    if not TELEGRAM_TOKEN:
        print("Ошибка: Токен Telegram не найден. Убедитесь, что файл telegram_token.txt существует.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    notification_service = NotificationService(bot)
    
    # Замените на реальный chat_id для теста
    test_user_id = 123456789 
    
    success = await notification_service.send_notification(
        user_id=test_user_id,
        message="Это тестовое уведомление от NotificationService."
    )
    
    if success:
        print("Тестовое уведомление успешно отправлено.")
    else:
        print("Не удалось отправить тестовое уведомление.")

if __name__ == "__main__":
    # Для запуска этого скрипта напрямую, убедитесь, что TELEGRAM_TOKEN доступен
    # и Django настроен для доступа к settings.
    # В реальном приложении этот сервис будет импортироваться и использоваться в других частях кода.
    print("Этот скрипт предназначен для импорта, а не для прямого запуска.")
    # Чтобы запустить main(), нужно настроить окружение Django.
    # asyncio.run(main())
