""" Test Catalog Task Get and Update """
import asyncio
import json
import logging
from aioresponses import aioresponses
import pytest
from catalog_mqtt_client.handlers import catalog_task
import configparser


logger = logging.getLogger(__name__)

def test_get():
    """ Test Get Method """
    headers = {"Content-Type": "application/json"}
    data = {'input': { 'jobs': [] }, 'state':'pending'}
    url = 'http://www.example.com/tasks/12345'
    config=configparser.ConfigParser()
    config['AUTH'] = {'x_rh_identity':'123'}
    ct = catalog_task.CatalogTask(config, url)

    with aioresponses() as mocked:
        mocked.get(
            url,
            status=200,
            body=json.dumps(data),
            headers=headers,
        )
        data = json.loads(asyncio.run(ct.get()))
        assert data['state'] == 'pending'
        

def test_get_fail():
    """ Test Get Method with exception"""
    url = 'http://www.example.com/tasks/12345'
    config=configparser.ConfigParser()
    config['AUTH'] = {'x_rh_identity':'123'}
    ct = catalog_task.CatalogTask(config, url)

    with aioresponses() as mocked:
        mocked.get(
            url,
            status=400,
            body="Kaboom",
        )
        with pytest.raises(Exception) as excinfo:
           asyncio.run(ct.get())
        assert "Status Code 400" in str(excinfo.value)

def test_update():
    """ Test Update Method """
    headers = {"Content-Type": "application/json"}
    data = {'input': { 'jobs': [] }, 'state':'ok'}
    url = 'http://www.example.com/tasks/12345'
    config=configparser.ConfigParser()
    config['AUTH'] = {'x_rh_identity':'123'}
    ct = catalog_task.CatalogTask(config, url)

    with aioresponses() as mocked:
        mocked.patch(
            url,
            status=200,
            body=json.dumps(data),
            headers=headers,
        )
        payload = {'name': 'Fred', 'age': 45}
        data = json.loads(asyncio.run(ct.update(payload)))
        assert data['state'] == 'ok'
        
def test_update_fail():
    """ Test Failure of Update Method """
    headers = {"Content-Type": "application/json"}
    data = {'input': { 'jobs': [] }, 'state':'ok'}
    url = 'http://www.example.com/tasks/12345'
    config=configparser.ConfigParser()
    config['AUTH'] = {'x_rh_identity':'123'}
    ct = catalog_task.CatalogTask(config, url)

    with aioresponses() as mocked:
        mocked.patch(
            url,
            status=400,
            body=json.dumps(data),
            headers=headers,
        )
        payload = {'name': 'Fred', 'age': 45}
        with pytest.raises(Exception) as excinfo:
           asyncio.run(ct.update(payload))
        assert "Status Code 400" in str(excinfo.value)
