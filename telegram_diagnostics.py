"""
Диагностика проблем с подключением к Telegram API
"""
import os
import requests
import socket
import ssl
import time
from urllib.parse import urlparse

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings

def test_dns_resolution():
    """Тест разрешения DNS"""
    print("=== Тест DNS разрешения ===")
    try:
        ip = socket.gethostbyname('api.telegram.org')
        print(f"✅ api.telegram.org разрешен в IP: {ip}")
        return True
    except Exception as e:
        print(f"❌ Ошибка DNS разрешения: {e}")
        return False

def test_tcp_connection():
    """Тест TCP подключения"""
    print("\\n=== Тест TCP подключения ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('api.telegram.org', 443))
        sock.close()
        
        if result == 0:
            print("✅ TCP подключение к api.telegram.org:443 успешно")
            return True
        else:
            print(f"❌ Не удалось подключиться к api.telegram.org:443, код: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка TCP подключения: {e}")
        return False

def test_ssl_handshake():
    """Тест SSL рукопожатия"""
    print("\\n=== Тест SSL рукопожатия ===")
    try:
        context = ssl.create_default_context()
        with socket.create_connection(('api.telegram.org', 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname='api.telegram.org') as ssock:
                print(f"✅ SSL подключение успешно")
                print(f"   Версия SSL: {ssock.version()}")
                print(f"   Шифр: {ssock.cipher()}")
                return True
    except Exception as e:
        print(f"❌ Ошибка SSL: {e}")
        return False

def test_http_request():
    """Тест HTTP запроса"""
    print("\\n=== Тест HTTP запроса ===")
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        print(f"Отправляем запрос на: {url[:50]}...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ HTTP запрос успешен!")
                print(f"   Имя бота: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                return True
            else:
                print(f"❌ Telegram API вернул ошибку: {data}")
                return False
        else:
            print(f"❌ HTTP статус: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут HTTP запроса (30 сек)")
        return False
    except requests.exceptions.SSLError as e:
        print(f"❌ Ошибка SSL в HTTP запросе: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Ошибка подключения в HTTP запросе: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка HTTP запроса: {e}")
        return False

def test_alternative_endpoints():
    """Тест альтернативных endpoints"""
    print("\\n=== Тест альтернативных endpoints ===")
    
    endpoints = [
        "https://api.telegram.org",
        "https://149.154.167.220",  # Один из IP Telegram
        "https://telegram.org"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Тестируем {endpoint}...")
            response = requests.get(endpoint, timeout=10, verify=False)
            print(f"   ✅ Доступен, статус: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Недоступен: {e}")

def test_proxy_settings():
    """Проверка настроек прокси"""
    print("\\n=== Проверка прокси ===")
    
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    proxy_found = False
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   Найдена переменная {var}: {value}")
            proxy_found = True
    
    if not proxy_found:
        print("   ✅ Прокси переменные не установлены")

def test_firewall():
    """Проверка возможной блокировки файрволом"""
    print("\\n=== Проверка файрвола ===")
    
    test_sites = [
        "https://google.com",
        "https://github.com",
        "https://httpbin.org/ip"
    ]
    
    for site in test_sites:
        try:
            response = requests.get(site, timeout=5)
            print(f"   ✅ {site}: доступен")
        except Exception as e:
            print(f"   ❌ {site}: недоступен - {e}")

def main():
    """Основная функция диагностики"""
    print("🔍 Диагностика подключения к Telegram API")
    print("=" * 50)
    
    print(f"Токен: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
    
    results = []
    results.append(("DNS", test_dns_resolution()))
    results.append(("TCP", test_tcp_connection()))
    results.append(("SSL", test_ssl_handshake()))
    results.append(("HTTP", test_http_request()))
    
    test_alternative_endpoints()
    test_proxy_settings()
    test_firewall()
    
    print("\\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
    
    success_count = 0
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\\nУспешных тестов: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("\\n🎉 Все тесты пройдены! Telegram API доступен.")
    elif success_count >= 2:
        print("\\n⚠️  Частичные проблемы с подключением.")
        print("   Возможные причины:")
        print("   - Нестабильное интернет-соединение")
        print("   - Временные проблемы с Telegram серверами")
        print("   - Блокировка на уровне провайдера")
    else:
        print("\\n🚨 Серьезные проблемы с подключением!")
        print("   Возможные решения:")
        print("   - Проверьте интернет-соединение")
        print("   - Проверьте настройки файрвола")
        print("   - Используйте VPN")
        print("   - Обратитесь к системному администратору")

if __name__ == '__main__':
    main()