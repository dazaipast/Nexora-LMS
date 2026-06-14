from services.auth_service import AuthManager
from services.user_service import UserService
from services.course_service import CourseService
from services.audit_service import AuditService
from services.stats_service import StatsService
from services.learning_service import LearningService
from services.report_service import ReportService
from services.material_service import MaterialService
from services.department_service import DepartmentService

__all__ = [
    "AuthManager", "UserService", "CourseService", "AuditService", "StatsService",
    "LearningService", "ReportService", "MaterialService", "DepartmentService",
]
