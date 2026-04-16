from ..repos.base_repo import ReadDbBaseRepo
from ..models.employee_model import ReadDbEmployeeCreateModel,ReadDbEmployeeReadModel,ReadDbEmployeeUpdateModel
from ..main import EMPLOYEES_COLLECTION
from typing import Optional,List,Any
from models.infra_models.readdb_model import BaseReadDbModel


class ReadDbEmployeeService(BaseReadDbModel):
    def __init__(self,payload:Any,conditions:dict):
        self.payload=payload
        self.conditions=conditions
        self.collection=EMPLOYEES_COLLECTION
        self.base_Repo_obj=ReadDbBaseRepo(collection=self.collection)
        # super.__init__(payload,conditions)

    
    async def create(self):
        if not isinstance(self.payload,ReadDbEmployeeCreateModel):
            return False

        data=self.payload.model_dump(mode="json",exclude_unset=True)
        return (await self.base_Repo_obj.create(data=data)).acknowledged
    
    async def update(self):
        if not isinstance(self.payload,ReadDbEmployeeUpdateModel):
            return False
        
        data=self.payload.model_dump(mode="json",exclude_unset=True)
        return (await self.base_Repo_obj.update(data=data,conditions=self.conditions))
    
    async def delete(self):
        return (await self.base_Repo_obj.delete(conditions=self.conditions))
    
    async def get(self,query:str,limit:Optional[int]=None,offset:Optional[int]=None):
        query=query.strip()
        queries={
            "$or":[
                {'employee_id':{'$regex':query,'$options':'i'}},
                {'account_id':{'$regex':query,'$options':'i'}},
                {'shop_id':{'$regex':query,'$options':'i'}},
                {'name':{'$regex':query,'$options':'i'}},
                {'email':{'$regex':query,'$options':'i'}},
                {'mobile_number':{'$regex':query,'$options':'i'}},
                {'added_by':{'$regex':query,'$options':'i'}},
                {'role':{'$regex':query,'$options':'i'}},
            ]
        }

        return await self.base_Repo_obj.get(queries=queries,offset=offset,limit=limit)
    
    async def getby_queries(self,queries:dict,limit:Optional[int]=None,offset:Optional[int]=None):
        return await self.base_Repo_obj.get(queries=queries,limit=limit,offset=offset)
    
    async def get_one(self,queries:dict):
        return await self.base_Repo_obj.get_one(queries=queries)
    
