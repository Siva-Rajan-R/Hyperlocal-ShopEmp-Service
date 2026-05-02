from enum import Enum

class EmployeeRoleEnums(str,Enum):
    USER='USER'
    ADMIN='ADMIN'
    SUPER_ADMIN='SUPER_ADMIN'

class EmployeeDepartmentEnums(str,Enum):
    SALES="SALES"
    BILLER="BILLER"
    MANAGER="MANAGER"