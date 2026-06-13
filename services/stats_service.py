from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from constants import EMPLOYEE_ROLE_ID, DEPT_HEAD_ROLE_ID
from models import User, Course, UserCourse, Department
from utils import query_user_progress_map, employee_performance_label


class StatsService:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_admin_summary(self, db):
        employees = (
            db.query(User)
            .filter(User.is_active.is_(True), User.role_id == EMPLOYEE_ROLE_ID)
            .count()
        )
        managers = (
            db.query(User)
            .filter(User.is_active.is_(True), User.role_id == DEPT_HEAD_ROLE_ID)
            .count()
        )
        active_courses = (
            db.query(Course).filter(Course.is_active.is_(True)).count()
        )
        learning_count = (
            db.query(func.count(func.distinct(UserCourse.user_id)))
            .join(Course, UserCourse.course_id == Course.id)
            .join(User, UserCourse.user_id == User.id)
            .filter(User.is_active.is_(True), Course.is_active.is_(True))
            .scalar()
        ) or 0

        enrollment_stats = self._enrollment_stats(db)
        return {
            "employees": employees,
            "learning_count": learning_count,
            "managers": managers,
            "active_courses": active_courses,
            "avg_progress": enrollment_stats["avg_progress"],
            "pass_rate": enrollment_stats["pass_rate"],
            "completed_count": enrollment_stats["completed_count"],
            "assigned_count": enrollment_stats["assigned_count"],
        }

    def get_department_summary(self, db, department_id, employee_stats=None):
        employees = (
            db.query(User)
            .filter(
                User.department_id == department_id,
                User.role_id == EMPLOYEE_ROLE_ID,
                User.is_active.is_(True),
            )
            .count()
        )
        active_courses = (
            db.query(Course)
            .filter(Course.department_id == department_id, Course.is_active.is_(True))
            .count()
        )
        learning_count = (
            db.query(func.count(func.distinct(UserCourse.user_id)))
            .join(Course, UserCourse.course_id == Course.id)
            .join(User, UserCourse.user_id == User.id)
            .filter(
                User.department_id == department_id,
                User.role_id == EMPLOYEE_ROLE_ID,
                User.is_active.is_(True),
                Course.is_active.is_(True),
            )
            .scalar()
        ) or 0

        enrollment_stats = self._enrollment_stats(db, department_id=department_id)
        if employee_stats is None:
            employee_stats = self.get_employee_stats(db, department_id=department_id)
        need_help = sum(1 for row in employee_stats if row["needs_help"])

        return {
            "employees": employees,
            "learning_count": learning_count,
            "active_courses": active_courses,
            "avg_progress": enrollment_stats["avg_progress"],
            "pass_rate": enrollment_stats["pass_rate"],
            "completed_count": enrollment_stats["completed_count"],
            "assigned_count": enrollment_stats["assigned_count"],
            "need_help_count": need_help,
        }

    def get_department_rows(self, db):
        depts = db.query(Department).order_by(Department.name).all()
        if not depts:
            return []

        dept_ids = [dept.id for dept in depts]

        employee_counts = dict(
            db.query(User.department_id, func.count(User.id))
            .filter(
                User.role_id == EMPLOYEE_ROLE_ID,
                User.is_active.is_(True),
                User.department_id.in_(dept_ids),
            )
            .group_by(User.department_id)
            .all()
        )

        course_counts = dict(
            db.query(Course.department_id, func.count(Course.id))
            .filter(Course.is_active.is_(True), Course.department_id.in_(dept_ids))
            .group_by(Course.department_id)
            .all()
        )

        learning_counts = dict(
            db.query(User.department_id, func.count(func.distinct(UserCourse.user_id)))
            .join(Course, UserCourse.course_id == Course.id)
            .join(User, UserCourse.user_id == User.id)
            .filter(
                User.role_id == EMPLOYEE_ROLE_ID,
                User.is_active.is_(True),
                Course.is_active.is_(True),
                User.department_id.in_(dept_ids),
            )
            .group_by(User.department_id)
            .all()
        )

        enrollment_by_dept = self._enrollment_stats_by_department(db, dept_ids)

        rows = []
        for dept in depts:
            stats = enrollment_by_dept.get(
                dept.id,
                {
                    "avg_progress": 0.0,
                    "pass_rate": 0.0,
                },
            )
            rows.append({
                "department_id": dept.id,
                "department_name": dept.name,
                "employees": employee_counts.get(dept.id, 0),
                "learning_count": learning_counts.get(dept.id, 0),
                "courses": course_counts.get(dept.id, 0),
                "avg_progress": stats["avg_progress"],
                "pass_rate": stats["pass_rate"],
            })
        return rows

    def get_course_stats(self, db, department_id=None):
        query = (
            db.query(Course)
            .options(joinedload(Course.department))
            .filter(Course.is_active.is_(True))
            .order_by(Course.title)
        )
        if department_id is not None:
            query = query.filter(Course.department_id == department_id)

        courses = query.all()
        if not courses:
            return []

        course_ids = [course.id for course in courses]
        enrollment_rows = (
            db.query(UserCourse.progress, UserCourse.course_id, Course.pass_threshold)
            .join(User, UserCourse.user_id == User.id)
            .join(Course, UserCourse.course_id == Course.id)
            .filter(
                UserCourse.course_id.in_(course_ids),
                User.is_active.is_(True),
                User.role_id == EMPLOYEE_ROLE_ID,
            )
            .all()
        )

        grouped = defaultdict(list)
        for progress, course_id, threshold in enrollment_rows:
            grouped[course_id].append((float(progress or 0), threshold))

        rows = []
        for course in courses:
            enrollments = grouped.get(course.id, [])
            assigned = len(enrollments)
            progresses = [value for value, _ in enrollments]
            passed = sum(
                1 for value, threshold in enrollments
                if value >= threshold
            )
            completed = sum(1 for value in progresses if value >= 100)
            avg_progress = sum(progresses) / len(progresses) if progresses else 0.0
            rows.append({
                "course_id": course.id,
                "title": course.title,
                "department_name": course.department.name if course.department else "—",
                "assigned": assigned,
                "passed": passed,
                "completed": completed,
                "avg_progress": avg_progress,
                "pass_threshold": course.pass_threshold,
            })
        return rows

    def get_employee_stats(self, db, department_id=None):
        query = (
            db.query(User)
            .options(joinedload(User.department))
            .filter(User.role_id == EMPLOYEE_ROLE_ID, User.is_active.is_(True))
            .order_by(User.full_name)
        )
        if department_id is not None:
            query = query.filter(User.department_id == department_id)

        employees = query.all()
        if not employees:
            return []

        user_ids = [emp.id for emp in employees]
        progress_map = query_user_progress_map(db, user_ids)
        assigned_counts = self._assigned_course_counts(db, user_ids)

        rows = []
        for employee in employees:
            progress = progress_map.get(employee.id, 0.0)
            rows.append({
                "user_id": employee.id,
                "full_name": employee.full_name,
                "position": employee.position,
                "department_name": (
                    employee.department.name if employee.department else "—"
                ),
                "progress": progress,
                "performance": employee_performance_label(progress),
                "needs_help": progress < 65,
                "assigned_courses": assigned_counts.get(employee.id, 0),
            })
        rows.sort(key=lambda row: row["progress"], reverse=True)
        return rows

    def get_problem_employees(self, db, department_id=None, employee_stats=None):
        if employee_stats is None:
            employee_stats = self.get_employee_stats(db, department_id=department_id)
        return [row for row in employee_stats if row["needs_help"]]

    def _assigned_course_counts(self, db, user_ids):
        if not user_ids:
            return {}
        rows = (
            db.query(UserCourse.user_id, func.count(UserCourse.id))
            .join(Course, UserCourse.course_id == Course.id)
            .filter(
                UserCourse.user_id.in_(user_ids),
                Course.is_active.is_(True),
            )
            .group_by(UserCourse.user_id)
            .all()
        )
        return {user_id: count for user_id, count in rows}

    def _enrollment_stats_by_department(self, db, department_ids):
        rows = (
            db.query(User.department_id, UserCourse.progress, Course.pass_threshold)
            .join(Course, UserCourse.course_id == Course.id)
            .join(User, UserCourse.user_id == User.id)
            .filter(
                User.is_active.is_(True),
                Course.is_active.is_(True),
                User.department_id.in_(department_ids),
            )
            .all()
        )

        grouped = defaultdict(list)
        for dept_id, progress, threshold in rows:
            grouped[dept_id].append((float(progress or 0), threshold))

        result = {}
        for dept_id, values in grouped.items():
            progresses = [progress for progress, _ in values]
            passed = sum(
                1 for progress, threshold in values
                if progress >= threshold
            )
            result[dept_id] = {
                "avg_progress": sum(progresses) / len(progresses),
                "pass_rate": passed / len(values) * 100,
            }
        return result

    def _enrollment_stats(self, db, department_id=None):
        query = (
            db.query(UserCourse.progress, Course.pass_threshold)
            .join(Course, UserCourse.course_id == Course.id)
            .join(User, UserCourse.user_id == User.id)
            .filter(User.is_active.is_(True), Course.is_active.is_(True))
        )
        if department_id is not None:
            query = query.filter(User.department_id == department_id)

        rows = query.all()
        if not rows:
            return {
                "assigned_count": 0,
                "completed_count": 0,
                "avg_progress": 0.0,
                "pass_rate": 0.0,
            }

        progresses = [float(progress or 0) for progress, _ in rows]
        passed = sum(
            1 for progress, threshold in rows
            if float(progress or 0) >= threshold
        )
        completed = sum(1 for progress in progresses if progress >= 100)
        return {
            "assigned_count": len(rows),
            "completed_count": completed,
            "avg_progress": sum(progresses) / len(progresses),
            "pass_rate": passed / len(rows) * 100,
        }
