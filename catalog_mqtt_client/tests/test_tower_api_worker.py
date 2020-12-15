""" Test Tower API Worker """
import queue
import asyncio
import json
import logging
from aioresponses import aioresponses
import pytest
from catalog_mqtt_client.handlers import tower_api_worker
import configparser
from test_data import TestData


class SimpleWriter:
    def __init__(self, prefix=None):
        self.data = "Nada, Zilch Zip"
        self.fname = "Nada"
        self.called = 0
        self.prefix = prefix
        self.prefixUsed = False

    async def write(self, data, fname):
        self.data = json.loads(data)
        self.fname = fname
        self.called += 1
        if self.prefix:
            self.prefixUsed = self.prefix in fname


@pytest.mark.asyncio
async def test_invalid_method():
    """ Test Invalid Method """
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.INVALID_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, None, work_queue)
    with pytest.raises(Exception) as excinfo:
        await worker.start()
    assert "Invalid method bad" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get():
    """ Test Get Method """
    writer = SimpleWriter("my_prefix")
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_PAYLOAD_SINGLE_PAGE)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(
            TestData.DEFAULT_JOB_TEMPLATES_LIST_URL,
            status=200,
            body=json.dumps(TestData.JOB_TEMPLATE_RESPONSE),
            headers=headers,
        )
        res = await worker.start()
        assert writer.data["count"] == 3
        assert writer.fname == "api/v2/job_templates/my_prefix1"
        assert writer.prefixUsed == True


@pytest.mark.asyncio
async def test_get_multiple_pages():
    """ Test Get Method Multiple Pages"""
    writer = SimpleWriter()
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_PAYLOAD_ALL_PAGES)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(
            TestData.JOB_TEMPLATES_LIST_URL,
            status=200,
            body=json.dumps(TestData.JOB_TEMPLATES_PAGE1_RESPONSE),
            headers=headers,
        )
        mocked.get(
            TestData.JOB_TEMPLATES_LIST_URL_PAGE_2,
            status=200,
            body=json.dumps(TestData.JOB_TEMPLATES_PAGE2_RESPONSE),
            headers=headers,
        )
        res = await worker.start()
        assert writer.data["count"] == 3
        assert writer.called == 2


@pytest.mark.asyncio
async def test_get_with_related():
    """ Test Get Method plus related"""
    writer = SimpleWriter("my_prefix")
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_PAYLOAD_FETCH_RELATED)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(
            TestData.DEFAULT_JOB_TEMPLATES_LIST_URL,
            status=200,
            body=json.dumps(TestData.JOB_TEMPLATE_RESPONSE),
            headers=headers,
        )
        mocked.get(
            TestData.SURVEY_URL,
            status=200,
            body=json.dumps(TestData.SURVEY_DATA),
            headers=headers,
        )
        res = await worker.start()
        assert writer.called == 2
        assert (
            writer.fname
            == f"api/v2/job_templates/{TestData.JOB_TEMPLATE_ID_1}/survey_spec/page1"
        )


@pytest.mark.asyncio
async def test_single_get_with_related():
    """ Test Single Get Method plus related"""
    writer = SimpleWriter("my_prefix")
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_PAYLOAD_SINGLE_RELATED)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(
            TestData.JOB_TEMPLATE_ID_1_URL,
            status=200,
            body=json.dumps(TestData.JOB_TEMPLATE_SINGLE_RESPONSE),
            headers=headers,
        )
        mocked.get(
            TestData.SURVEY_URL,
            status=200,
            body=json.dumps(TestData.SURVEY_DATA),
            headers=headers,
        )
        res = await worker.start()
        assert writer.called == 2
        assert (
            writer.fname
            == f"api/v2/job_templates/{TestData.JOB_TEMPLATE_ID_1}/survey_spec/page1"
        )


@pytest.mark.asyncio
async def test_get_400():
    """ test get method - 400"""
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_PAYLOAD_SINGLE_PAGE)
    worker = tower_api_worker.TowerApiWorker(TestData.config, None, work_queue)
    with aioresponses() as mocked:
        mocked.get(TestData.DEFAULT_JOB_TEMPLATES_LIST_URL, status=400, body="BAD DATA")
        with pytest.raises(Exception) as excinfo:
            await worker.start()
        assert "BAD DATA" in str(excinfo.value)


@pytest.mark.asyncio
async def test_post():
    """ Test Post Method """
    writer = SimpleWriter()
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_POST_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.post(
            TestData.JOB_TEMPLATE_POST_URL,
            status=200,
            body=json.dumps(TestData.JOB_TEMPLATE_POST_RESPONSE),
            headers=headers,
        )
        res = await worker.start()
        assert writer.data["status"] == "successful"
        assert writer.data["url"] == "/api/v2/jobs/500"
        assert writer.data["artifacts"] == {
            "expose_to_cloud_redhat_com__snow_ticket": 12345
        }


@pytest.mark.asyncio
async def test_post_400():
    """ Test Post Method - 400"""
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_POST_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, None, work_queue)
    with aioresponses() as mocked:
        mocked.post(
            TestData.JOB_TEMPLATE_POST_URL, status=400, body="BAD DATA",
        )
        with pytest.raises(Exception) as excinfo:
            await worker.start()
        assert "BAD DATA" in str(excinfo.value)


@pytest.mark.asyncio
async def test_launch():
    """ Test Launch Method """
    writer = SimpleWriter()
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_LAUNCH_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.post(
            TestData.JOB_TEMPLATE_POST_URL,
            status=200,
            body=json.dumps(TestData.JOB_1_RUNNING),
            headers=headers,
        )
        mocked.get(
            TestData.JOB_MONITOR_URL,
            status=200,
            body=json.dumps(TestData.JOB_1_SUCCESSFUL),
            headers=headers,
        )
        res = await worker.start()
        assert writer.data["status"] == "successful"
        assert writer.called == 2
        assert writer.data["url"] == "/api/v2/jobs/500"
        assert writer.data["artifacts"] == {
            "expose_to_cloud_redhat_com__snow_ticket": 12345
        }


@pytest.mark.asyncio
async def test_launch_400():
    """ Test Launch Method - 400 """
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_TEMPLATE_LAUNCH_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, None, work_queue)
    with aioresponses() as mocked:
        mocked.post(
            TestData.JOB_TEMPLATE_POST_URL, status=400, body="BAD DATA",
        )
        with pytest.raises(Exception) as excinfo:
            await worker.start()
        assert "BAD DATA" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_huge_artifact():
    """ Test Get Method with Huge Artifact"""
    writer = SimpleWriter()
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_GET_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(
            TestData.JOB_MONITOR_URL,
            status=200,
            body=json.dumps(TestData.JOB_1_SUCCESSFUL_HUGE),
            headers=headers,
        )
        with pytest.raises(Exception) as excinfo:
            await worker.start()
        assert "Artifacts is over 1024 bytes" in str(excinfo.value)


@pytest.mark.asyncio
async def test_monitor():
    """ Test Monitor Method """
    writer = SimpleWriter()
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_MONITOR_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(TestData.config, writer, work_queue)
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(
            TestData.JOB_MONITOR_URL,
            status=200,
            body=json.dumps(TestData.JOB_1_RUNNING),
            headers=headers,
        )
        mocked.get(
            TestData.JOB_MONITOR_URL,
            status=200,
            body=json.dumps(TestData.JOB_1_SUCCESSFUL),
            headers=headers,
        )
        res = await worker.start()
        assert writer.data["status"] == "successful"
        assert writer.called == 1
        assert writer.data["url"] == "/api/v2/jobs/500"
        assert writer.data["artifacts"] == {
            "expose_to_cloud_redhat_com__snow_ticket": 12345
        }


@pytest.mark.asyncio
async def test_monitor_400():
    """ Test Monitor Method - 400"""
    writer = SimpleWriter()
    work_queue = asyncio.Queue()
    await work_queue.put(TestData.JOB_MONITOR_PAYLOAD)
    worker = tower_api_worker.TowerApiWorker(
        TestData.no_verify_config, writer, work_queue
    )
    headers = {"Content-Type": "application/json"}
    with aioresponses() as mocked:
        mocked.get(TestData.JOB_MONITOR_URL, status=400, body="BAD DATA")
        with pytest.raises(Exception) as excinfo:
            await worker.start()
        assert "BAD DATA" in str(excinfo.value)
