""" Message Handler Tests """
import json
import pytest
from test_data import TestData
from catalog_mqtt_client.handlers import tower_api_worker
from catalog_mqtt_client.handlers import catalog_task
from catalog_mqtt_client.handlers import tar_writer
from catalog_mqtt_client.handlers import message_handler


@pytest.mark.asyncio
async def test_start(mocker):
    """ Test the Start Method in the Message Handler """
    payload = {"url": "http://www.example.com/task/123"}
    task_info = {
        "input": {
            "response_format": "tar",
            "upload_url": "http://www.example.com/upload",
            "jobs": [{"href_slug": "/api/v2/job/1", "method": "get"}],
        }
    }

    mocker.patch.object(tower_api_worker.TowerApiWorker, "start", autospec=True)
    mocker.patch.object(
        catalog_task.CatalogTask,
        "get",
        autospec=True,
        return_value=json.dumps(task_info),
    )
    mocker.patch.object(tar_writer.TarWriter, "flush", autospec=True)

    msg = message_handler.MessageHandler(TestData.config, json.dumps(payload))
    await msg.start()
