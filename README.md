# Nexora LMS

**Nexora LMS** — desktop-платформа корпоративного обучения для клиник и компаний с разветвлённой организационной структурой. Приложение помогает управлять курсами, отслеживать прогресс сотрудников и формировать отчёты для администраторов и руководителей подразделений.

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-Private-lightgrey)

---

## Возможности

| Роль | Что доступно |
|------|----------------|
| **Администратор** | Обзор KPI, подразделения, пользователи, курсы, журнал аудита, CSV-экспорт |
| **Руководитель** | Сотрудники отдела, курсы, статистика, назначение обучения |
| **Сотрудник** | Личный кабинет, прогресс, рекомендации, прохождение курсов и тестов |

### Ключевой функционал

- Управление подразделениями, пользователями и курсами
- Назначение курсов с дедлайнами и порогом сдачи
- Модульная структура курсов: файлы и тесты (DOCX)
- Адаптивные рекомендации и блок «Сегодня вам»
- Журнал аудита действий
- Экспорт отчётов в CSV
- Сборка в один `.exe` — Python на машине пользователя не нужен

---

## Быстрый старт

### Требования

- Windows 10/11
- Python 3.13+ (только для разработки)

### Установка для разработки

```powershell
git clone https://github.com/dazaipast/Nexora-LMS.git
cd Nexora-LMS
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py
```

### Сборка exe

```powershell
build_exe.bat
```

Готовый файл: `dist\Nexora LMS.exe`

При первом запуске рядом с exe создаются:
- `nexora_lms.db` — база данных
- `course_materials/` — материалы курсов

> Если ранее использовался LearnMate Core, база `learnmate_core.db` автоматически переименуется в `nexora_lms.db`.

---

## Демо-аккаунты

| Роль | Email | Пароль |
|------|-------|--------|
| Администратор | n.makanina@rami-clinic.ru | admin123 |
| Руководитель | i.ivanov@rami-clinic.ru | manager123 |
| Сотрудник | a.petrova@rami-clinic.ru | employee123 |

Демо-аккаунты восстанавливаются при каждом запуске приложения.

---

## Тестирование

```powershell
venv\Scripts\python test_smoke.py
```

Smoke-тесты проверяют авторизацию, статистику, сервисы, парсер тестов и UI для всех ролей.

---

## Структура проекта

```
├── main.py                 # Точка входа
├── database.py             # SQLite, миграции, демо-данные
├── models.py               # SQLAlchemy-модели
├── constants.py            # Константы и настройки бренда
├── services/               # Бизнес-логика
├── ui/                     # PyQt6 интерфейс
├── hooks/                  # PyInstaller hooks
├── test_smoke.py           # Smoke-тесты
├── build_exe.bat           # Сборка exe
└── LearnMateCore.spec      # Конфигурация PyInstaller
```

---

## Технологии

- **Python 3.13**, **PyQt6** — desktop UI
- **SQLAlchemy** + **SQLite** — хранение данных
- **bcrypt** — хеширование паролей
- **PyInstaller** — упаковка в exe

---

## Релизы

Скачать последнюю версию: [Releases](https://github.com/dazaipast/Nexora-LMS/releases)

---

## Автор

**dazaipast** — [GitHub](https://github.com/dazaipast)
