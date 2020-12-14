""" Test Tower API Worker """
import pdb
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
    def __init__(self):
        self.data = "Nada, Zilch Zip"
        self.fname = "Nada"
        self.called = 0

    async def write(self, data, fname):
        self.data = json.loads(data)
        self.fname = fname
        self.called += 1

@pytest.mark.asyncio
async def test_start_get():
    """ Test Get Method """
    writer = SimpleWriter()
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
        assert writer.data['count'] == 3
        assert writer.fname == 'api/v2/job_templates/page1'

@pytest.mark.asyncio
async def test_start_post():
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
        assert writer.data['status'] == 'successful'
        assert writer.data['url'] == '/api/v2/jobs/500'
        assert writer.data['artifacts'] == {'expose_to_cloud_redhat_com__snow_ticket': 12345}

@pytest.mark.asyncio
async def test_start_launch():
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
        assert writer.data['status'] == 'successful'
        assert writer.called == 2
        assert writer.data['url'] == '/api/v2/jobs/500'
        assert writer.data['artifacts'] == {'expose_to_cloud_redhat_com__snow_ticket': 12345}
