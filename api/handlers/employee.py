from infras.primary_db.services.employee_service import EmployeeService,AsyncSession
from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,GetEmployeeByIdSchema,GetAllEmployeesSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema,DeleteEmployeeSchema,SendVerifyEmployeeSchema
from schemas.v1.response_schemas.user_schemas.employee_schemas import EmployeeGetResponseSchema,EmployeeCreateResponseSchema,EmployeeDeleteResponseSchema,EmployeeUpdateResponseSchema
from core.data_formats.enums.employee_enums import EmployeeRoleEnums
from infras.primary_db.services.shop_service import ShopService
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from typing import Optional
from icecream import ic
from core.utils.token_utils import generate_verification_token, decode_verification_token
from core.utils.email_sender import send_verification_email

class HandleEmployeeRequest:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def create(self,data:CreateEmployeeSchema,user_id:str):
        # Check if employee already exists by email in this shop
        is_emp_exists=await EmployeeService(session=self.session).verify_employee(data=VerifyEmployeeSchema(shop_id=data.shop_id,email=data.email))
        if is_emp_exists['exists']:
            raise HTTPException(
                status_code=409,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating Employee",
                    description="Employee already exists in this shop",
                    success=False,
                    status_code=409
                )
            )
        
        res = await EmployeeService(session=self.session).create(data=data, owner_user_id=user_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Employee invited successfully. Verification email sent.",
                    status_code=201,
                    success=True
                ),
                data=EmployeeCreateResponseSchema(**res)
            )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponseTypDict(
                msg="Error : Creating Employee",
                description="Database insert failed",
                success=False,
                status_code=500
            )
        )


    async def update(self,data:UpdateEmployeeSchema):
        res=await EmployeeService(session=self.session).update(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee Updated Successfully",
                status_code=200,
                success=True
            ),
            data=EmployeeUpdateResponseSchema(**res) if res else None
        )
    

    async def send_verify(self,data:SendVerifyEmployeeSchema):
        data_tocheck=GetEmployeeByIdSchema(id=data.id,shop_id=data.shop_id)
        get_res=await EmployeeService(session=self.session).getby_id(data=data_tocheck)
        ic(get_res)
        if get_res:
            if not get_res['accepted']:
                token = generate_verification_token(employee_id=data.id, shop_id=data.shop_id)
                await send_verification_email(email=get_res['email'], name=get_res['name'], token=token)
            
                return SuccessResponseTypDict(
                        detail=BaseResponseTypDict(
                            msg="Employee invited successfully. Verification email sent.",
                            status_code=201,
                            success=True
                        )
                    )

        raise HTTPException(
            status_code=400,
            detail=ErrorResponseTypDict(
                msg="Error : Sending Verfification",
                description="Sending email failed",
                success=False,
                status_code=400
            )
        )

    

    async def delete(self,data:DeleteEmployeeSchema):
        res=await EmployeeService(session=self.session).delete(data=data)
        ic(res)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    msg="Employee Deleted Successfully",
                    success=True,
                    status_code=200
                ),
                data=EmployeeDeleteResponseSchema(**res) if res else None
            )
        
        raise HTTPException(
            status_code=404,
            detail=ErrorResponseTypDict(
                msg="Error : Deleting employee",
                description="Invalid Employee data (id,shop_id)",
                success=False,
                status_code=404
            )
        )
    
    async def get_all(self,data:GetAllEmployeesSchema):
        res=await EmployeeService(session=self.session).get(data=data)
        ic(res)
        
        if data.offset in (0, 1):
            data_to_send = {
                "overall_datas": res.get("overall_datas", {}),
                "datas": [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]
            }
        else:
            data_to_send = [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employees fetched successfully",
                status_code=200,
                success=True
            ),

            data=data_to_send
        )
    
    async def getby_id(self,data:GetEmployeeByIdSchema):
        res=await EmployeeService(session=self.session).getby_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=EmployeeGetResponseSchema(**res) if res else None
        )
    
    async def getby_shopid(self,data:GetEmployeeByShopIdSchema):
        res=await EmployeeService(session=self.session).getby_shopid(data=data)
        
        if data.offset in (0, 1):
            data_to_send = {
                "overall_datas": res.get("overall_datas", {}),
                "datas": [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]
            }
        else:
            data_to_send = [EmployeeGetResponseSchema(**r) for r in res.get("datas", [])]

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=data_to_send
        )
    
    async def search(self,q:str,limit:int):
        # We can implement a simple PG-based search if needed, fallback to empty for now
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee search fetched successfully",
                status_code=200,
                success=True
            ),
            data=[]
        )