""" Test Json Writer Update """
import json
import pytest
from test_data import TestData
from catalog_mqtt_client.handlers import json_writer


# pylint: disable=R0903
class SimpleCatalogTask:
    """ Stub Class to Check incoming data"""

    def __init__(self):
        self.data = {}

    async def update(self, data):
        """ Update method to catch data"""
        self.data = data


@pytest.mark.asyncio
async def test_flush():
    """ Test Flush Method """
    c_task = SimpleCatalogTask()
    writer = json_writer.JSONWriter(TestData.config, c_task)
    await writer.flush()

    assert (c_task.data["state"]) == "completed"
    assert (c_task.data["status"]) == "ok"


@pytest.mark.asyncio
async def test_flush_errors():
    """ Test Flush Errors Method """
    c_task = SimpleCatalogTask()
    writer = json_writer.JSONWriter(TestData.config, c_task)
    await writer.flush_errors("kaboom")

    assert (c_task.data["state"]) == "completed"
    assert (c_task.data["status"]) == "error"


def test_cleanup():
    """ Test Cleanup """
    c_task = SimpleCatalogTask()
    writer = json_writer.JSONWriter(TestData.config, c_task)
    writer.cleanup()


@pytest.mark.asyncio
async def test_write():
    """ Test Write Method"""
    c_task = SimpleCatalogTask()
    writer = json_writer.JSONWriter(TestData.config, c_task)
    result = {"name": "Fred Flintstone"}
    await writer.write(json.dumps(result), "file1")

    assert (c_task.data["state"]) == "running"
    assert (c_task.data["output"]["name"]) == "Fred Flintstone"
    assert (c_task.data["status"]) == "ok"
