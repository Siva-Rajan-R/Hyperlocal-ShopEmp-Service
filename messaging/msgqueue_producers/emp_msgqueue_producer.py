from schemas.v1.request_schemas.employee_schemas import CreateEmployeeSchema,UpdateEmployeeSchema,DeleteEmployeeSchema
from infras.primary_db.services.employee_service import EmployeeService
from infras.primary_db.main import AsyncShopEmployeeLocalSession
from hyperlocal_platform.core.enums.saga_state_enum import SagaStepsValueEnum
from sqlalchemy.ext.asyncio import AsyncSession
from ..main import RabbitMQMessagingConfig
from icecream import ic


class MessagingQueueEmployeeProducer:
    def __init__(self,headers:dict,payload:dict,saga_datas:dict):
        self.headers=headers
        self.payload=payload
        self.saga_datas=saga_datas
        
    async def create_employee(self):
        accounts_data={}
        try:
            ic(self.headers,self.payload,self.saga_datas)
            saga_datas:dict=self.saga_datas
            data:dict=saga_datas['data']

            employees_data=data['employees']
            rb_msg=RabbitMQMessagingConfig(rabbitMQ_connection=await RabbitMQMessagingConfig.get_rabbitmq_connection())


            if saga_datas['execution']['step']=="ACCOUNT_VERIFICATION":
                accounts_data:dict|str=data.get("accounts","not_found")
                if accounts_data=="not_found":
                    return {"response":False,'execution':None}
                
                if not accounts_data['exists']:
                    await rb_msg.publish_event(
                        routing_key="accounts.service.routing.key",
                        payload=self.payload,
                        headers={
                            **self.headers,
                            'entity_name':'create_account',
                            'service_name':'ACCOUNTS',
                            'body':{
                                'name':employees_data['name'],
                                'mobile_number':employees_data['mobile_number'],
                                'email':employees_data['email'],
                                'source':'INVENTORY-EMPLOYEE-SERVICE',
                                'accessed':['HYPERLOCAL_SERVICE']
                            }
                        },
                        exchange_name="accounts.service.exchange"
                    )
                
                    return {'response':True,'execution':{'next_step':'ACCOUNT_CREATION','service':'ACCOUNTS'}}
                
            if saga_datas['execution']['step']=="ACCOUNT_CREATION":
                accounts_data:dict|str=data.get("accounts","not_found")
                if accounts_data=="not_found" or not accounts_data:
                    return {"response":False,'execution':None}
                

            data_toadd=CreateEmployeeSchema(**employees_data)
            ic(data_toadd)
            async with AsyncShopEmployeeLocalSession() as session:
                res=await EmployeeService(session=session).create(data=data_toadd,user_id=employees_data['account_id'],account_id=accounts_data['id'])
                ic(res)
                if not res:
                    await rb_msg.publish_event(
                        routing_key="accounts.service.routing.key",
                        payload=self.payload,
                        headers={
                            **self.headers,
                            'entity_name':'delete_account',
                            'service_name':'ACCOUNTS',
                            'body':{
                                'account_id':accounts_data['id']
                            }
                        },
                        exchange_name="accounts.service.exchange"
                    )
                
                    return {'response':True,'execution':{'next_step':'ACCOUNT_DELETE','service':'ACCOUNTS'}}
                
            return {'response':True,'execution':{'next_step':'','service':''}}
        
        except Exception as e:
            ic(f"A Unknown Exception Occur : {e}")
            if accounts_data:
                await rb_msg.publish_event(
                    routing_key="accounts.service.routing.key",
                    payload=self.payload,
                    headers={
                        **self.headers,
                        'entity_name':'delete_account',
                        'service_name':'ACCOUNTS',
                        'body':{
                            'account_id':accounts_data['id']
                        }
                    },
                    exchange_name="accounts.service.exchange"
                )
        
                return {'response':True,'execution':{'next_step':'ACCOUNT_DELETE','service':'ACCOUNTS'}}
            return {'response':False,'execution':None}
             
            
            



        