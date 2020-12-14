"""The Main Application, waits for Messages to arrive from the
   MQTT Broker and spawns of a handler to talk to the Ansible Tower
   via REST API and send back responsed to cloud.redhat.com
 """
import os
import asyncio
import configparser
import logging
import sys
import signal
from urllib.parse import urlparse
import paho.mqtt.client as mqtt
from catalog_mqtt_client.handlers import message_handler

logger = logging.getLogger(__name__)


class App:
    """ The App Class, listens for MQTT messages
    Once the Message is received it fetches the Catalog task from
    cloud.redhat.com and then looks at the task input field to see
    the list of requests
    """

    def __init__(self):
        """ Constructor """
        self.config = configparser.ConfigParser()
        self.message_count = 0
        if os.getenv('CATALOG_MQTT_CONF') is None:
            raise Exception("Please set env variable CATALOG_MQTT_CONF")

        self.config.read(os.getenv('CATALOG_MQTT_CONF'))

        p_url = urlparse(self.config["MQTT_BROKER"]["URL"])
        self.host = p_url.hostname
        self.port = p_url.port
        self.topic = "out/" + self.config["MQTT_BROKER"]["UUID"]
        self.qos = 0
        self.client = mqtt.Client(self.config["MQTT_BROKER"]["UUID"])

    def connect(self):
        """Connect to the MQTT Broker"""
        try:
            logger.info(
                "Attempting to connect to MQTT Broker %s:%s", self.host, self.port
            )
            self.client.on_connect = self.on_connect
            self.client.connect(self.host, self.port)
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.subscribe(self.topic, self.qos)
        except Exception:
            logger.error("Error connecting to MQTT Broker", exc_info=True)
            logger.error("Failed to connect to %s:%s", self.host, self.port)
            raise

    def on_disconnect(self, _client, _userdata, mqtt_rc):
        """When we disconnect from MQTT Broker this callback is invoked"""
        logger.info(
            "Disconnecting reason %s after %d messages", str(mqtt_rc), self.message_count
        )

    def on_connect(self, client, _userdata, _flags, mqtt_rc):
        """When connection is established with MQTT Broker this callback is invoked"""
        if mqtt_rc == 0:
            client.connected_flag = True  # set flag
            logger.info(
                "Successfully connected to MQTT Broker %s",
                self.config["MQTT_BROKER"]["url"],
            )
        else:
            logger.error(
                "Could not connect to MQTT Broker %s code %s",
                self.config["MQTT_BROKER"]["url"],
                str(mqtt_rc),
            )
            client.bad_connection_flag = True

    def on_message(self, _client, _userdata, message):
        """When a new MQTT Message comes in this callback is invoked"""
        self.message_count = self.message_count + 1
        try:
            logger.info("MQTT Message Received")
            handler = message_handler.MessageHandler(
                self.config, str(message.payload.decode("utf-8"))
            )
            asyncio.run(handler.start())
            logger.info("MQTT Message Finished Processing")
        except:
            logger.error("Error handling MQTT Message", exc_info=True)

    def start(self):
        """Start the MQTT Client Loop on a separate thread"""
        logger.info("Starting MQTT Client Worker")
        self.client.loop_start()

    def stop(self):
        """Stop the MQTT Client loop"""
        logger.info("Stopping MQTT Client Worker")
        self.client.loop_stop()

    def signal_handler(self, signum, _frame):
        """Signale handler to stop the MQTT Client loop"""
        logger.info("Received Signal %s", str(signum))
        signal.signal(signum, signal.SIG_IGN)
        self.stop()
        sys.exit(0)


async def run():
    """ Run the App forever till we catch a signal to end """
    app = App()
    signal.signal(signal.SIGINT, app.signal_handler)
    app.connect()
    app.start()
    while True:
        await asyncio.sleep(10)
