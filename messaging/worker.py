from .main import RabbitMQMessagingConfig,ExchangeType
from .controllers.controller import ConsumersHandler
import asyncio

async def worker():
    rabbitmq_conn=await RabbitMQMessagingConfig.get_rabbitmq_connection()
    rabbitmq_msg_obj=RabbitMQMessagingConfig(rabbitMQ_connection=rabbitmq_conn)

    # Exchanges
    exchanges=[
        {'name':'accounts.employees.employees.exchange','exc_type':ExchangeType.TOPIC},
        {'name':'inventory.inventory.shops.exchange','exc_type':ExchangeType.TOPIC}
    ]

    for exchange in exchanges:
        await rabbitmq_msg_obj.create_exchange(name=exchange['name'],exchange_type=exchange['exc_type'])

    # Queues
    queues=[
        {'exc_name':'accounts.employees.employees.exchange','q_name':'accounts.employees.employees.queue','r_key':'accounts.employees.*.*.v1'},
        {'exc_name':'inventory.inventory.shops.exchange','q_name':'inventory.inventory.shops.queue','r_key':'inventory.inventory.*.*.v1'}
    ]

    for queue in queues:
        queue=await rabbitmq_msg_obj.create_queue(
            exchange_name=queue['exc_name'],
            queue_name=queue['q_name'],
            routing_key=queue['r_key']
        )

    # Consumers
    consumers=[
        {'q_name':'accounts.employees.employees.queue','handler':ConsumersHandler.main_handler},
        {'q_name':'inventory.inventory.shops.queue','handler':ConsumersHandler.main_handler}
    ]

    for consumer in consumers:
        await rabbitmq_msg_obj.consume_event(queue_name=consumer['q_name'],handler=consumer['handler'])

    await asyncio.Event().wait()

    



    