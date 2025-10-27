# bots/handlers/error_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bots.utils.message_utils import reply_with_menu
from bots.menu_manager import MenuManager

logger = logging.getLogger(__name__)


async def handle_unexpected_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает сообщения, которые не соответствуют ожидаемому состоянию диалога.
    """
    user_text = update.message.text
    logger.warning(f"Пользователь {update.effective_user.id} ввел '{user_text}' в неожиданном состоянии.")

    error_text = """
🤔 Хм, я не ожидал этого сейчас. Кажется, мы сбились с пути.

Давайте вернемся в главное меню. Используйте кнопки ниже для навигации.
"""

    await reply_with_menu(update, error_text, menu_type='main')
    return ConversationHandler.END


async def handle_text_instead_of_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает текстовые сообщения, когда ожидается нажатие на кнопку.
    """
    help_text = """
💡 Пожалуйста, используйте кнопки для ответа, чтобы я мог вас понять.

Кнопки расположены внизу экрана и позволяют легко ориентироваться в меню.

Если вы не видите кнопок, нажмите /start для перезапуска бота.
"""

    await reply_with_menu(update, help_text, menu_type='main')


async def handle_conversation_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает таймаут диалога.
    """
    logger.warning(f"Диалог с пользователем {update.effective_user.id} превысил время ожидания.")

    timeout_text = """
⏰ Время диалога истекло.

Диалог был автоматически завершен из-за неактивности.

Возвращаю вас в главное меню. Вы всегда можете начать заново!
"""

    await reply_with_menu(update, timeout_text, menu_type='main')
    return ConversationHandler.END


async def handle_database_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ошибки базы данных.
    """
    logger.error("Ошибка базы данных при обработке запроса", exc_info=context.error)

    db_error_text = """
🗄️ Произошла ошибка при работе с базой данных.

Пожалуйста, попробуйте повторить действие через несколько минут.

Если ошибка повторяется, обратитесь к администратору @hr_admin
"""

    await reply_with_menu(update, db_error_text, menu_type='main')


async def handle_network_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает сетевые ошибки.
    """
    logger.error("Сетевая ошибка при обработке запроса", exc_info=context.error)

    network_error_text = """
🌐 Произошла сетевая ошибка.

Пожалуйста, проверьте ваше интернет-соединение и попробуйте снова.

Если проблема сохраняется, попробуйте позже.
"""

    await reply_with_menu(update, network_error_text, menu_type='main')


async def handle_authorization_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ошибки авторизации.
    """
    logger.warning(f"Ошибка авторизации для пользователя {update.effective_user.id}")

    auth_error_text = """
🔐 Ошибка авторизации.

Возможно, ваш профиль не полностью настроен или требуется повторная авторизация.

Пожалуйста, используйте команду /start для повторной авторизации.

Если проблема сохраняется, обратитесь к администратору.
"""

    await reply_with_menu(update, auth_error_text, menu_type='main')


async def handle_validation_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ошибки валидации данных.
    """
    logger.warning(f"Ошибка валидации данных от пользователя {update.effective_user.id}")

    validation_error_text = """
📝 Ошибка ввода данных.

Пожалуйста, проверьте введенные данные и попробуйте снова.

Убедитесь, что:
• Используете правильный формат
• Не превышаете ограничения по длине
• Используете только разрешенные символы
"""

    await reply_with_menu(update, validation_error_text, menu_type='main')


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Глобальный обработчик ошибок. Логирует ошибки и сообщает пользователю.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Определяем тип ошибки для более точного сообщения
    error = context.error
    error_message = "⚙️ Ой, что-то пошло не так."

    if hasattr(error, '__class__'):
        error_class = error.__class__.__name__
        
        if 'Database' in error_class or 'Connection' in error_class:
            error_message = "🗄️ Временные проблемы с базой данных. Попробуйте позже."
        elif 'Network' in error_class or 'Timeout' in error_class:
            error_message = "🌐 Проблемы с сетью. Проверьте соединение и попробуйте снова."
        elif 'Authorization' in error_class or 'Permission' in error_class:
            error_message = "🔐 Ошибка доступа. Используйте /start для повторной авторизации."
        elif 'Validation' in error_class:
            error_message = "📝 Ошибка в данных. Проверьте ввод и попробуйте снова."

    error_message += "\n\nЯ уже сообщил об ошибке разработчикам. Пожалуйста, попробуйте еще раз через некоторое время."

    # Попытка уведомить пользователя
    if isinstance(update, Update) and update.effective_message:
        try:
            await reply_with_menu(update.effective_message, error_message, menu_type='main')
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {e}")


def setup_error_handlers(application):
    """
    Настройка обработчиков ошибок для приложения.
    """
    # Добавляем глобальный обработчик ошибок
    application.add_error_handler(global_error_handler)
    
    logger.info("Обработчики ошибок настроены")