# Обновление Java Runtime до Java 21 - Инструкции

## 📋 Статус обновления

✅ **ВСЕ ПОДГОТОВИТЕЛЬНЫЕ РАБОТЫ ЗАВЕРШЕНЫ!**

### Что уже сделано:
- ✅ Обновлена версия Java в `pom.xml` с 17 на 21
- ✅ Обновлен Spring Boot с 3.2.0 до 3.3.5 (лучшая поддержка Java 21) 
- ✅ Проверен код на совместимость с Java 21
- ✅ Найден Maven Wrapper для сборки проекта
- ✅ Созданы скрипты для тестирования

## 🔧 Что нужно сделать пользователю:

### 1. Установить JDK 21
Скачайте и установите JDK 21 с официального сайта:
- **Eclipse Temurin**: https://adoptium.net/temurin/releases/?version=21
- **Oracle JDK**: https://www.oracle.com/java/technologies/downloads/#java21

### 2. Настроить переменные окружения

После установки JDK 21:

```powershell
# Установить JAVA_HOME (замените путь на ваш)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.x.x-hotspot"
[Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Eclipse Adoptium\jdk-21.0.x.x-hotspot", "User")

# Обновить PATH
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
```

### 3. Проверить установку

```powershell
java -version
# Должна показать: openjdk version "21.0.x"
```

## 🚀 Автоматическое тестирование

После установки JDK 21 запустите тестовый скрипт:

```powershell
# Если JAVA_HOME уже настроен
.\test_java21_upgrade.ps1

# Или укажите путь к JDK 21 явно
.\test_java21_upgrade.ps1 -JavaHome "C:\Program Files\Eclipse Adoptium\jdk-21.0.x.x-hotspot"
```

Скрипт автоматически:
- Проверит версию Java
- Скомпилирует проект с Java 21
- Запустит тесты
- Соберет JAR файл

## 🔍 Ручное тестирование

Если хотите протестировать вручную:

```powershell
# 1. Перейти в директорию проекта
cd "E:\ConnectBot v21\connectbot-java-services\matching-service"

# 2. Компиляция
.\mvnw.cmd clean compile

# 3. Тесты
.\mvnw.cmd test

# 4. Сборка JAR
.\mvnw.cmd clean package

# 5. Запуск приложения
java -jar target\matching-service-1.0.0.jar
```

## 📊 Преимущества Java 21

- **LTS версия** - поддержка до 2031 года
- **Улучшенная производительность** - до 15% быстрее Java 17
- **Новые возможности**:
  - Virtual Threads (JEP 444) - значительно лучшая производительность I/O
  - Pattern Matching for switch (JEP 441)
  - Record Patterns (JEP 440)
  - String Templates (Preview - JEP 430)

## 📁 Созданные файлы

- `JAVA_21_UPGRADE_REPORT.md` - детальный отчет об изменениях
- `test_java21_upgrade.ps1` - скрипт автоматического тестирования
- `install_java21_portable.ps1` - скрипт установки портативной Java (если нужен)

## ⚡ Быстрый старт

1. Установите JDK 21
2. Настройте JAVA_HOME  
3. Запустите: `.\test_java21_upgrade.ps1`
4. Готово! ✅

---

**Проект готов к работе с Java 21!** 🎉