from models import User, Department, AuditLog


class DepartmentService:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def can_create(self, actor):
        return actor.is_role("main_admin")

    def create_department(self, actor_id, name, description=None):
        name = name.strip()
        if not name:
            raise ValueError("Укажите название подразделения")
        if len(name) > 100:
            raise ValueError("Название не должно превышать 100 символов")

        description = (description or "").strip() or None

        with self.db_manager.session_scope() as db:
            actor = db.query(User).filter(User.id == actor_id).first()
            if not actor:
                raise ValueError("Текущий пользователь не найден")
            if not self.can_create(actor):
                raise PermissionError("Недостаточно прав для создания подразделения")

            if db.query(Department).filter(Department.name == name).first():
                raise ValueError("Подразделение с таким названием уже существует")

            department = Department(name=name, description=description)
            db.add(department)
            db.flush()

            db.add(AuditLog(
                user_id=actor.id,
                department_id=department.id,
                action="create_department",
                details=f"Создано подразделение: {department.name}",
            ))
            db.commit()
            return department.id
