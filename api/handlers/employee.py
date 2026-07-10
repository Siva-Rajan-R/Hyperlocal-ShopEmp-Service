from infras.primary_db.services.employee_service import EmployeeService,AsyncSession
from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,GetEmployeeByIdSchema,GetAllEmployeesSchema,GetEmployeeByShopIdSchema,VerifyEmployeeSchema,DeleteEmployeeSchema,SendVerifyEmployeeSchema,VerifyEmployeeTokenSchema
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
        # Check if the email being added belongs to the shop owner
        try:
            from schemas.v1.request_schemas.shop_schemas import GetShopByIdSchema
            shop_detail = await ShopService(session=self.session).getby_id(GetShopByIdSchema(shop_id=data.shop_id))
            if shop_detail:
                owner_user_id = shop_detail.get("user_id")
                if owner_user_id:
                    from sqlalchemy import select
                    from infras.primary_db.models.user_model import Users
                    owner_stmt = select(Users.email).where(Users.id == owner_user_id)
                    owner_email = (await self.session.execute(owner_stmt)).scalar_one_or_none()
                    
                    if owner_email and owner_email.strip().lower() == data.email.strip().lower():
                        raise HTTPException(
                            status_code=400,
                            detail=ErrorResponseTypDict(
                                msg="Error : Creating Employee",
                                description="Shop owner cannot be added as an employee",
                                success=False,
                                status_code=400
                            )
                        )
        except HTTPException:
            raise
        except Exception as e:
            ic(f"Error checking shop owner: {e}")

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
                data=res
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
            data=res
        )
    

    async def verify_token(self,data:VerifyEmployeeTokenSchema):
        res = await EmployeeService(session=self.session).accept_employee(token=data.token)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee invitation accepted and verified successfully",
                status_code=200,
                success=True
            ),
            data=res
        )

    async def send_verify(self,data:SendVerifyEmployeeSchema):
        data_tocheck=GetEmployeeByIdSchema(id=data.id,shop_id=data.shop_id)
        get_res=await EmployeeService(session=self.session).getby_id(data=data_tocheck)
        ic(get_res)
        if get_res:
            if get_res['accepted']:
                return SuccessResponseTypDict(
                    detail=BaseResponseTypDict(
                        msg="Employee is already verified.",
                        status_code=200,
                        success=True
                    ),
                    data=get_res
                )

            token = generate_verification_token(employee_id=data.id, shop_id=data.shop_id)
            sent = await send_verification_email(email=get_res['email'], name=get_res['name'], token=token)
            if sent:
                return SuccessResponseTypDict(
                    detail=BaseResponseTypDict(
                        msg="Employee verification email sent successfully.",
                        status_code=201,
                        success=True
                    ),
                    data={"id": data.id, "shop_id": data.shop_id}
                )

        raise HTTPException(
            status_code=400,
            detail=ErrorResponseTypDict(
                msg="Error : Sending Verification",
                description="Employee not found, already invalid, or email delivery failed",
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
                data=res
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

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employees fetched successfully",
                status_code=200,
                success=True
            ),

            data=res
        )
    
    async def getby_id(self,data:GetEmployeeByIdSchema):
        res=await EmployeeService(session=self.session).getby_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    
    async def getby_shopid(self,data:GetEmployeeByShopIdSchema):
        res=await EmployeeService(session=self.session).getby_shopid(data=data)
        

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Employee fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
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