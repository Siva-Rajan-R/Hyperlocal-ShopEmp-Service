from enum import Enum

class EmployeeRoleEnums(str,Enum):
    OWNER='OWNER'
    SUPER_ADMIN='SUPER_ADMIN'
    ADMIN='ADMIN'
    BILLER='BILLER'
    USER='USER'

class EmployeeDepartmentEnums(str,Enum):
    SALES="SALES"
    BILLER="BILLER"
    MANAGER="MANAGER"