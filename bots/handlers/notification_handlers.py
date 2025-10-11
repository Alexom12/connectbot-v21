# Заглушка для тестирования
async def send_telegram_message(telegram_id, message):
    """Заглушка для отправки Telegram сообщений во время тестирования"""
    print(f"[TELEGRAM] Отправка сообщения пользователю {telegram_id}:")
    print(f"  {message[:100]}...")
    return True