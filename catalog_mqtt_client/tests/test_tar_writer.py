""" Test Writer Tests """
import os
import tempfile
import json
import pytest
from aioresponses import aioresponses
from test_data import TestData
from catalog_mqtt_client.handlers import tar_writer


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
    writer = tar_writer.TarWriter(TestData.config, c_task, TestData.UPLOAD_URL)
    result = {"name": "Fred Flintstone"}
    await writer.write(json.dumps(result), "file1")
    with aioresponses() as mocked:
        mocked.post(TestData.UPLOAD_URL, status=200, body=json.dumps({"name": "Fred"}))
        await writer.flush()

    assert (c_task.data["state"]) == "completed"
    assert (c_task.data["status"]) == "ok"
    writer.cleanup()


@pytest.mark.asyncio
async def test_flush_errors():
    """ Test Flush Errors Method """
    c_task = SimpleCatalogTask()
    dirname, tgzfile = prep_test()
    writer = tar_writer.TarWriter(
        TestData.config, c_task, TestData.UPLOAD_URL, dirname, tgzfile
    )
    await writer.flush_errors("kaboom")
    writer.cleanup()

    assert (c_task.data["state"]) == "completed"
    assert (c_task.data["status"]) == "error"


def test_cleanup():
    """ Test Cleanup """
    c_task = SimpleCatalogTask()
    dirname, tgzfile = prep_test()
    writer = tar_writer.TarWriter(
        TestData.config, c_task, TestData.UPLOAD_URL, dirname, tgzfile
    )
    writer.cleanup()
    assert not os.path.exists(dirname)
    assert not os.path.exists(tgzfile)


@pytest.mark.asyncio
async def test_write():
    """ Test Write Method"""
    c_task = SimpleCatalogTask()
    dirname, tgzfile = prep_test()
    writer = tar_writer.TarWriter(
        TestData.no_verify_config, c_task, TestData.UPLOAD_URL, dirname, tgzfile
    )
    result = {"name": "Fred Flintstone"}
    await writer.write(json.dumps(result), "file1")
    assert os.path.exists(dirname + "/file1")
    writer.cleanup()


def prep_test():
    """ Create temporary directory and filename """
    dirname = tempfile.TemporaryDirectory(prefix="test").name
    tgzfile = tempfile.NamedTemporaryFile(prefix="test", suffix=".tgz").name
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(dirname + "/demo.txt", "w") as file_handle:
        file_handle.write("Hello World\n")
    return dirname, tgzfile
