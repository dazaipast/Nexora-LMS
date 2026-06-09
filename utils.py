import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import func

from constants import (
    MODULES_PER_COURSE,
    DEFAULT_MODULES_PER_COURSE,
    MIN_MODULES_PER_COURSE,
    MAX_MODULES_PER_COURSE,
    AUDIT_ACTION_LABELS,
    EVENT_ACTION_ICONS,
    ALLOWED_MATERIAL_EXTENSIONS,
    MAX_MATERIAL_SIZE_BYTES,
    COURSE_TYPES,
    DEFAULT_COURSE_TYPE,
    PROGRESS_GROUP_ADAPTATION,
    PROGRESS_GROUP_GENERAL,
    PROGRESS_GROUP_PROFESSIONAL,
)
from models import User, UserCourse, Department


def format_percent(value):
    return f"{round(value or 0):.0f}%"


def avg_progress(values):
    return sum(values) / len(values) if values else 0.0


def query_avg_progress(db, user_ids=None, department_id=None):
    query = db.query(func.avg(UserCourse.progress)).join(User, User.id == UserCourse.user_id)
    if user_ids is not None:
        query = query.filter(UserCourse.user_id.in_(user_ids))
    if department_id is not None:
        query = query.filter(User.department_id == department_id, User.is_active.is_(True))
    return float(query.scalar() or 0)


def query_user_progress_map(db, user_ids):
    if not user_ids:
        return {}
    rows = (
        db.query(UserCourse.user_id, func.avg(UserCourse.progress))
        .filter(UserCourse.user_id.in_(user_ids))
        .group_by(UserCourse.user_id)
        .all()
    )
    return {user_id: float(progress) for user_id, progress in rows}


def course_type_label(course_type):
    info = COURSE_TYPES.get(course_type or DEFAULT_COURSE_TYPE)
    if not info:
        info = COURSE_TYPES[DEFAULT_COURSE_TYPE]
    return info["label"]


def course_progress_group(course):
    if not course:
        return PROGRESS_GROUP_PROFESSIONAL
    course_type = getattr(course, "course_type", None) or DEFAULT_COURSE_TYPE
    info = COURSE_TYPES.get(course_type, COURSE_TYPES[DEFAULT_COURSE_TYPE])
    return info["progress_group"]


def validate_course_type(course_type):
    if course_type not in COURSE_TYPES:
        labels = ", ".join(info["label"] for info in COURSE_TYPES.values())
        raise ValueError(f"Выберите тип курса: {labels}")
    return course_type


def infer_course_type_from_title(title):
    lowered = (title or "").lower()
    if "адаптация" in lowered:
        return "adaptation"
    if any(keyword in lowered for keyword in ("услуг", "битрикс", "знан")):
        return "general_knowledge"
    if "возражен" in lowered:
        return "objection_handling"
    if "практик" in lowered or "продаж" in lowered:
        return "practice"
    return DEFAULT_COURSE_TYPE


def split_employee_progress(user_courses):
    groups = {
        PROGRESS_GROUP_ADAPTATION: [],
        PROGRESS_GROUP_GENERAL: [],
        PROGRESS_GROUP_PROFESSIONAL: [],
    }
    for uc in user_courses:
        groups[course_progress_group(uc.course)].append(uc.progress)
    return (
        int(avg_progress(groups[PROGRESS_GROUP_ADAPTATION])),
        int(avg_progress(groups[PROGRESS_GROUP_GENERAL])),
        int(avg_progress(groups[PROGRESS_GROUP_PROFESSIONAL])),
    )


def course_module_count(course=None):
    if course is None:
        return DEFAULT_MODULES_PER_COURSE
    count = getattr(course, "module_count", None)
    return count if count else DEFAULT_MODULES_PER_COURSE


def validate_module_count(module_count):
    value = int(module_count)
    if not MIN_MODULES_PER_COURSE <= value <= MAX_MODULES_PER_COURSE:
        raise ValueError(
            f"Количество этапов должно быть от {MIN_MODULES_PER_COURSE} "
            f"до {MAX_MODULES_PER_COURSE}"
        )
    return value


def validate_module_index(module_index, module_count):
    value = int(module_index)
    if not 1 <= value <= module_count:
        raise ValueError(f"Этап должен быть от 1 до {module_count}")
    return value


def module_progress_step(module_count=None):
    count = module_count or MODULES_PER_COURSE
    return 100.0 / count


def current_module_index(progress, module_count=None):
    count = module_count or MODULES_PER_COURSE
    if progress >= 100:
        return count
    return min(count, int(progress / module_progress_step(count)) + 1)


def modules_completed(progress, module_count=None):
    count = module_count or MODULES_PER_COURSE
    if progress >= 100:
        return count
    return int(progress / module_progress_step(count))


def build_module_content(course, module_index, module_count):
    description = (course.description or "Изучите материалы курса.").strip()
    topics = [
        "Введение и цели обучения",
        "Теоретическая часть",
        "Практические примеры",
        "Типовые ситуации и ошибки",
        "Итоговое закрепление",
    ]
    topic = topics[(module_index - 1) % len(topics)]
    return (
        f"Этап {module_index} из {module_count}: {topic}\n\n"
        f"{description}\n\n"
        f"Задание: изучите материал этапа и нажмите «Завершить этап», "
        f"чтобы перейти дальше."
    )


def employee_performance_label(progress):
    value = float(progress or 0)
    if value >= 95:
        return "отличник"
    if value >= 80:
        return "хорошо"
    if value >= 65:
        return "нормально"
    if value > 0:
        return "нужна помощь"
    return "не начал"


def format_ratio(passed, total):
    return f"{passed}/{total}"


def course_pass_status(progress, pass_threshold):
    if progress >= 100:
        return "Завершён"
    if progress >= pass_threshold:
        return "Сдан"
    if progress > 0:
        return "В процессе"
    return "Не начат"


def format_audit_timestamp(value):
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y %H:%M")


def format_history_date(value):
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y")


def audit_action_label(action):
    return AUDIT_ACTION_LABELS.get(action, action)


def format_event_line(entry):
    icon = EVENT_ACTION_ICONS.get(entry["action"], "•")
    timestamp = format_audit_timestamp(entry.get("created_at"))
    label = audit_action_label(entry["action"]).lower()
    details = entry.get("details") or ""
    if details:
        text = f"{icon} [{timestamp}] {entry['user_name']}: {label} — {details}"
    else:
        text = f"{icon} [{timestamp}] {entry['user_name']}: {label}"
    return text


def save_csv_report(file_path, title, actor_name, sections):
    """Сохраняет отчёт в CSV (UTF-8 с BOM, разделитель ';' для Excel в RU)."""
    with open(file_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow([title])
        writer.writerow([f"Сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
        writer.writerow([f"Пользователь: {actor_name}"])
        writer.writerow([])

        for section in sections:
            writer.writerow([section["name"]])
            writer.writerow(section["headers"])
            for row in section["rows"]:
                writer.writerow(row)
            writer.writerow([])


def format_file_size(size_bytes):
    size = float(size_bytes or 0)
    if size < 1024:
        return f"{int(size)} Б"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} КБ"
    return f"{size / (1024 * 1024):.1f} МБ"


def material_extension(path):
    return Path(path).suffix.lower()


def is_allowed_material_file(path):
    return material_extension(path) in ALLOWED_MATERIAL_EXTENSIONS


def validate_material_file(path):
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"Файл не найден: {file_path.name}")
    extension = material_extension(file_path)
    if extension not in ALLOWED_MATERIAL_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_MATERIAL_EXTENSIONS))
        raise ValueError(
            f"Формат «{extension or 'без расширения'}» не поддерживается.\n"
            f"Допустимые форматы: {allowed}"
        )
    size = file_path.stat().st_size
    if size > MAX_MATERIAL_SIZE_BYTES:
        raise ValueError(
            f"Файл «{file_path.name}» слишком большой "
            f"({format_file_size(size)}). Максимум: {format_file_size(MAX_MATERIAL_SIZE_BYTES)}"
        )
    if size == 0:
        raise ValueError(f"Файл «{file_path.name}» пустой")
    return size


def load_departments_for_actor(db, actor_user, fixed_department_id=None):
    if fixed_department_id:
        query = db.query(Department).filter(Department.id == fixed_department_id)
    elif actor_user.is_role('department_head'):
        query = db.query(Department).filter(Department.id == actor_user.department_id)
    else:
        query = db.query(Department).order_by(Department.name)
    return query.all()
