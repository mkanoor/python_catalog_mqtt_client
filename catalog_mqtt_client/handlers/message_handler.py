""" This module handles the incoming MQTT Message"""
import logging
import json
import asyncio
from catalog_mqtt_client.handlers import catalog_task
from catalog_mqtt_client.handlers import tar_writer
from catalog_mqtt_client.handlers import json_writer
from catalog_mqtt_client.handlers import tower_api_worker

logger = logging.getLogger(__name__)


class MessageHandler:
    """ MQTT MessageHandler
        It first gets the Catalog Task from cloud.redhat.com
        Then for each request in the Input it adds them to a queue
        Creates multiple workers to deal with the work in the queue
    """

    def __init__(self, config, payload):
        logger.debug("Request Payload is %s", payload)
        self.request = json.loads(payload)
        self.config = config
        self.c_task = catalog_task.CatalogTask(self.config, self.request["url"])

    async def start(self):
        """ Start processing the incoming MQTT Message """
        data = await self.c_task.get()
        work = json.loads(data)["input"]
        logger.debug(work)
        current_writer = self.get_writer(work)

        try:
            work_queue = asyncio.Queue()
            for job in work["jobs"]:
                logger.debug(job)
                await work_queue.put(job)

            worker_1 = tower_api_worker.TowerApiWorker(
                self.config, current_writer, work_queue
            )
            worker_2 = tower_api_worker.TowerApiWorker(
                self.config, current_writer, work_queue
            )

            await asyncio.gather(
                asyncio.create_task(worker_1.start()),
                asyncio.create_task(worker_2.start()),
            )
            await current_writer.flush()
        except Exception as exp:
            await current_writer.flush_errors([str(exp)])
            raise
        finally:
            current_writer.cleanup()

    def get_writer(self, work):
        """ Create an appropriate writer object based on the response format """
        if work["response_format"] == "tar":
            return tar_writer.TarWriter(self.config, self.c_task, work["upload_url"])

        # By default we support the JSON Writer
        return json_writer.JSONWriter(self.config, self.c_task)
