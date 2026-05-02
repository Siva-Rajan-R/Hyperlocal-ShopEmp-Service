from pydantic import BaseModel

class MessageHeaderModel(BaseModel):
    entity_name:str
    service_name:str
    body:dict
    reply_key:str
    reply_exchange:str
    reply_entity_name:str
    saga_id:str

    model_config={
        "extra":'allow'
    }