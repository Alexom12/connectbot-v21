# bots/services/user_service.py

from telegram import User

def format_user_for_logging(user: User) -> str:
    """
    Форматирует информацию о пользователе для логирования.
    """
    if not user:
        return "Anonymous"
    
    user_info = f"ID: {user.id}"
    if user.username:
        user_info += f", @{user.username}"
    if user.full_name:
        user_info += f", Name: {user.full_name}"
        
    return user_info
