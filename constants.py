ROLE_CODES = {'main_admin': 1, 'department_head': 2, 'employee': 3}
ROLE_NAMES = {1: "Главный администратор", 2: "Руководитель", 3: "Сотрудник"}
MAIN_ADMIN_ROLE_ID = ROLE_CODES['main_admin']
DEPT_HEAD_ROLE_ID = ROLE_CODES['department_head']
EMPLOYEE_ROLE_ID = ROLE_CODES['employee']

MIN_PASSWORD_LENGTH = 6
DEFAULT_DEADLINE_DAYS = 30
DEFAULT_PASS_THRESHOLD = 80
DEFAULT_MODULES_PER_COURSE = 5
MIN_MODULES_PER_COURSE = 1
MAX_MODULES_PER_COURSE = 20
MODULES_PER_COURSE = DEFAULT_MODULES_PER_COURSE
MAX_MATERIAL_SIZE_BYTES = 50 * 1024 * 1024

PROGRESS_GROUP_ADAPTATION = "adaptation"
PROGRESS_GROUP_GENERAL = "general_knowledge"
PROGRESS_GROUP_PROFESSIONAL = "professional"

COURSE_TYPES = {
    "adaptation": {
        "label": "Адаптация",
        "progress_group": PROGRESS_GROUP_ADAPTATION,
    },
    "general_knowledge": {
        "label": "Общие знания",
        "progress_group": PROGRESS_GROUP_GENERAL,
    },
    "objection_handling": {
        "label": "Обработка возражений",
        "progress_group": PROGRESS_GROUP_PROFESSIONAL,
    },
    "practice": {
        "label": "Практика",
        "progress_group": PROGRESS_GROUP_PROFESSIONAL,
    },
    "special_skills": {
        "label": "Специальные навыки",
        "progress_group": PROGRESS_GROUP_PROFESSIONAL,
    },
}

DEFAULT_COURSE_TYPE = "special_skills"

PRACTICE_COURSE_TYPE = "practice"
QUIZ_FILE_EXTENSION = ".docx"

ALLOWED_MATERIAL_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".rtf", ".csv",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mp3", ".wav",
    ".zip", ".rar", ".7z",
}

MODULE_MATERIALS_HEADERS = ["Этап", "Файл", "Размер", "Загрузил"]

COURSE_TABLE_HEADERS = [
    "Название", "Тип", "Отдел", "Создатель", "Этапов", "Срок (дн.)",
    "Порог %", "Материалы", "Статус",
]
STAT_VALUE_STYLE = "font-size: 32px; font-weight: 700; color: {color};"
STAT_TITLE_STYLE = "font-size: 13px; font-weight: 600; color: #1A2B3C;"
STAT_DESC_STYLE = "font-size: 11px; color: #6B7C8F;"
STAT_CARD_STYLE = (
    "background: #FFFFFF; border-radius: 12px; "
    "border: 1px solid #D8DEE6;"
)
STAT_COLORS = ("#0D6E6E", "#2563EB", "#7C3AED", "#2E7D5B")

DEPT_STATS_HEADERS = [
    "Отдел", "Сотрудников", "Обучается", "Курсов", "Прогресс", "Успеваемость",
]
COURSE_STATS_HEADERS = [
    "Курс", "Назначено", "Сдано", "Завершено", "Ср. прогресс",
]
ADMIN_COURSE_STATS_HEADERS = [
    "Курс", "Отдел", "Назначено", "Сдано", "Завершено", "Ср. прогресс",
]
EMPLOYEE_STATS_HEADERS = [
    "ФИО", "Должность", "Отдел", "Курсов", "Прогресс", "Оценка",
]
DEPT_EMPLOYEE_STATS_HEADERS = [
    "ФИО", "Должность", "Курсов", "Прогресс", "Оценка",
]
PROBLEM_EMPLOYEE_HEADERS = [
    "ФИО", "Отдел", "Прогресс", "Оценка", "Курсов",
]
HISTORY_HEADERS = [
    "Курс", "Назначен", "Начат", "Завершён", "Прогресс", "Статус",
]

AUDIT_LOG_LIMIT = 200
EVENT_FEED_LIMIT = 8

AUDIT_ACTION_LABELS = {
    "login": "Вход в систему",
    "logout": "Выход из системы",
    "create_user": "Создание пользователя",
    "deactivate_user": "Деактивация пользователя",
    "delete_user": "Удаление пользователя",
    "change_department": "Смена отдела",
    "create_course": "Создание курса",
    "update_course": "Изменение курса",
    "deactivate_course": "Удаление курса",
    "assign_course": "Назначение курса",
    "complete_module": "Пройден модуль",
    "complete_module_quiz": "Сдан тест этапа",
    "complete_course": "Завершение курса",
    "add_course_material": "Добавление материала к курсу",
    "delete_course_material": "Удаление материала курса",
}

EVENT_ACTION_ICONS = {
    "login": "→",
    "logout": "←",
    "create_user": "+",
    "deactivate_user": "⚠",
    "delete_user": "⚠",
    "change_department": "↔",
    "create_course": "+",
    "update_course": "↔",
    "deactivate_course": "⚠",
    "assign_course": "→",
    "complete_module": "→",
    "complete_module_quiz": "✓",
    "complete_course": "✓",
    "add_course_material": "+",
    "delete_course_material": "⚠",
}
