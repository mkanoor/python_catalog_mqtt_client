""" Message Handler Tests """
import json
import pytest
from unittest.mock import patch
from test_data import TestData
from catalog_mqtt_client.handlers import tower_api_worker
from catalog_mqtt_client.handlers import catalog_task
from catalog_mqtt_client.handlers import tar_writer
from catalog_mqtt_client.handlers import message_handler


@pytest.mark.asyncio
@patch("catalog_mqtt_client.handlers.tar_writer.TarWriter.flush")
@patch("catalog_mqtt_client.handlers.catalog_task.CatalogTask.get")
@patch("catalog_mqtt_client.handlers.tower_api_worker.TowerApiWorker.start")
async def test_start_with_tar_writer(start_mock, get_mock, flush_mock):
    """ Test the Start Method in the Message Handler with Tar Writer"""
    task_info = {
           "input": {
               "response_format": "tar",
               "upload_url": "http://www.example.com/upload",
               "jobs": [{"href_slug": "/api/v2/job/1", "method": "get"}],
           }
    }
    get_mock.return_value = json.dumps(task_info)

    payload = {"url": "http://www.example.com/task/123"}
    msg = message_handler.MessageHandler(TestData.config, json.dumps(payload))
    await msg.start()
    start_mock.assert_called()
    get_mock.assert_called_once()
    flush_mock.assert_called_once()

@pytest.mark.asyncio
@patch("catalog_mqtt_client.handlers.json_writer.JSONWriter.flush")
@patch("catalog_mqtt_client.handlers.catalog_task.CatalogTask.get")
@patch("catalog_mqtt_client.handlers.tower_api_worker.TowerApiWorker.start")
async def test_start_with_json_writer(start_mock, get_mock, flush_mock):
    """ Test the Start Method in the Message Handler with JSON Writer"""
    task_info = {
           "input": {
               "response_format": "json",
               "upload_url": "http://www.example.com/upload",
               "jobs": [{"href_slug": "/api/v2/job/1", "method": "get"}],
           }
    }
    get_mock.return_value = json.dumps(task_info)

    payload = {"url": "http://www.example.com/task/123"}
    msg = message_handler.MessageHandler(TestData.config, json.dumps(payload))
    await msg.start()

    start_mock.assert_called()
    get_mock.assert_called_once()
    flush_mock.assert_called_once()

@pytest.mark.asyncio
@patch("catalog_mqtt_client.handlers.json_writer.JSONWriter.flush_errors")
@patch("catalog_mqtt_client.handlers.json_writer.JSONWriter.flush")
@patch("catalog_mqtt_client.handlers.catalog_task.CatalogTask.get")
@patch("catalog_mqtt_client.handlers.tower_api_worker.TowerApiWorker.start")
async def test_start_with_json_writer_exception(start_mock, get_mock, flush_mock, flush_error_mock):
    """ Test the Start Method in the Message Handler with JSON Writer"""
    task_info = {
           "input": {
               "response_format": "json",
               "upload_url": "http://www.example.com/upload",
               "jobs": [{"href_slug": "/api/v2/job/1", "method": "get"}],
           }
    }
    get_mock.return_value = json.dumps(task_info)
    start_mock.side_effect = Exception("Kaboom")

    payload = {"url": "http://www.example.com/task/123"}
    msg = message_handler.MessageHandler(TestData.config, json.dumps(payload))
    with pytest.raises(Exception) as excinfo:
        await msg.start()
    assert "Kaboom" in str(excinfo.value)

    start_mock.assert_called()
    flush_error_mock.assert_called_once_with(['Kaboom'])
    flush_mock.assert_not_called()
