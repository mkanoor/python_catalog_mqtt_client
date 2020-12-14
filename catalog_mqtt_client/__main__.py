"""Start the App."""
import os
import logging
import logging.config
import asyncio

if os.getenv('CATALOG_MQTT_CONF') is None:
    raise Exception("Please set env variable CATALOG_MQTT_CONF")

logging.config.fileConfig('/Users/madhukanoor/devsrc/python_catalog_mqtt_client/catalog_mqtt_client.conf')

from catalog_mqtt_client import app
if __name__ == "__main__":
    asyncio.run(app.run())
