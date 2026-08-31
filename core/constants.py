from enum import Enum


class LoanType(str, Enum):
    HOME_LOAN = "Home Loan"
    LOAN_AGAINST_PROPERTY = "Loan Against Property"


class EmploymentType(str, Enum):
    SALARIED = "Salaried"
    SELF_EMPLOYED = "Self Employed"


class BREStatus(str, Enum):
    ELIGIBLE = "Eligible"
    NOT_ELIGIBLE = "Not Eligible"
    PENDING = "Pending"


class UserRole(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    VIEWER = "Viewer"


class RuleOperator(str, Enum):
    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    EQ = "=="
    NEQ = "!="


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
