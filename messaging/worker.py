from .main import RabbitMQMessagingConfig,ExchangeType
from .controllers.producer_controller import producer_main_controller
from .controllers.service_controller import service_main_controller
import asyncio

async def worker():
    rabbitmq_conn=await RabbitMQMessagingConfig.get_rabbitmq_connection()
    rabbitmq_msg_obj=RabbitMQMessagingConfig(rabbitMQ_connection=rabbitmq_conn)

    # Exchanges
    exchanges=[
        {'name':'shops.service.exchange','exc_type':ExchangeType.DIRECT},
        {'name':'shops.producer.exchange','exc_type':ExchangeType.DIRECT},

        {'name':'employees.service.exchange','exc_type':ExchangeType.DIRECT},
        {'name':'employees.producer.exchange','exc_type':ExchangeType.DIRECT},
    ]

    for exchange in exchanges:
        await rabbitmq_msg_obj.create_exchange(name=exchange['name'],exchange_type=exchange['exc_type'])

    # Queues
    queues=[
        {'exc_name':'shops.service.exchange','q_name':'shops.service.queue','r_key':'shops.service.routing.key'},
        {'exc_name':'shops.producer.exchange','q_name':'shops.producer.queue','r_key':'shops.producer.routing.key'},

        {'exc_name':'employees.service.exchange','q_name':'employees.service.queue','r_key':'employees.service.routing.key'},
        {'exc_name':'employees.producer.exchange','q_name':'employees.producer.queue','r_key':'employees.producer.routing.key'},
    ]

    for queue in queues:
        queue=await rabbitmq_msg_obj.create_queue(
            exchange_name=queue['exc_name'],
            queue_name=queue['q_name'],
            routing_key=queue['r_key']
        )

    # Consumers
    consumers=[
        {'q_name':'employees.service.queue','handler':service_main_controller},
        {'q_name':'shops.service.queue','handler':service_main_controller},

        {'q_name':'employees.producer.queue','handler':producer_main_controller},
        {'q_name':'shops.producer.queue','handler':producer_main_controller}
        
    ]

    for consumer in consumers:
        await rabbitmq_msg_obj.consume_event(queue_name=consumer['q_name'],handler=consumer['handler'])

    await asyncio.Event().wait()


if __name__=="__main__":
    asyncio.run(worker())

    



    