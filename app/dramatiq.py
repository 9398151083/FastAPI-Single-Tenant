import os
from dotenv import load_dotenv
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
load_dotenv()

def set_host():
    print(os.getenv("RABBITMQ_HOST"))
    rabbitmq_broker = RabbitmqBroker(
        host=os.getenv("RABBITMQ_HOST"),
    )
    dramatiq.set_broker(rabbitmq_broker)

set_host()
