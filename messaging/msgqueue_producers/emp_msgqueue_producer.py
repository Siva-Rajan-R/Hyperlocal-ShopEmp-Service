from icecream import ic

class MessagingQueueEmployeeProducer:
    def __init__(self,headers:dict,payload:dict,saga_datas:dict):
        self.headers=headers
        self.payload=payload
        self.saga_datas=saga_datas
        
    async def create_employee(self):
        # Saga flow is deprecated and handled locally now
        ic("create_employee saga flow is deprecated")
        return {'response':True,'execution':{'next_step':'','service':''}}