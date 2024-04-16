"""
Use RabbitMq to connect multiple fossa nodes to distribute and jointly run sub-tasks.

The code is here is largely taken from https://github.com/Aye-Aye-Dev/Fossa/blob/main/examples/rabbit_mq.py
where you will find a better explanation of what's going on.


This could be built and run like this-

docker build -t fossa-worker .

docker run \
--env RABBITMQ_URL="amqp://guest:guest@172.17.0.2" \
--detach \
fossa-worker
"""

import os

from fossa import run_fossa, BaseConfig
from fossa.control.rabbit_mq.message_exchange import RabbitMx
from fossa.control.rabbit_mq.process import RabbitMqProcessor
from example_etl import PartitionedExampleEtl


class FossaConfig(BaseConfig):
    ACCEPTED_MODEL_CLASSES = [PartitionedExampleEtl]

    # e.g. "amqp://guest:guest@192.168.0.1"
    broker_url = os.environ["RABBITMQ_URL"]
    ISOLATED_PROCESSOR = RabbitMqProcessor(broker_url=broker_url)
    MESSAGE_BROKER_MANAGERS = [RabbitMx(broker_url=broker_url)]


if __name__ == "__main__":
    run_fossa(FossaConfig)
