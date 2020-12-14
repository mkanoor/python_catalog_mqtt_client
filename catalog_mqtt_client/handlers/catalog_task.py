"""Catalog Task Module, fetches and patch Catalog Task objects """
import logging
import aiohttp
logger = logging.getLogger(__name__)


class CatalogTask:
    """ Get & Update Catalog Task object"""
    VALID_POST_CODES = [200, 201, 202, 204]

    def __init__(self, config, url):
        self.config = config
        self.url = url
        self.headers = {}
        self.headers["x-rh-identity"] = self.config["AUTH"]["x_rh_identity"]

    async def get(self):
        """ Get the Catalog Task object from cloud.redhat.com"""
        logger.debug("Getting Task %s", self.url)
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.url) as response:
                logger.debug("GET Status %d", response.status)
                logger.debug("GET Content-type: %s", response.headers['Content-Type'])

                data = await response.text()
                if response.status != 200:
                    logger.error("GET %s Status Code %d", self.url, response.status)
                    logger.error(data)
                    raise Exception("GET %s Status Code %d" % (self.url, response.status))

                return data

    async def update(self, data):
        """ Patch the Catalog Task object in cloud.redhat.com"""
        logger.debug("Updating Task %s", self.url)
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.patch(self.url, json=data) as response:
                logger.debug("PATCH Status %d", response.status)
                result = await response.text()

                if response.status not in self.VALID_POST_CODES:
                    logger.error("PATCH %s Status Code %d", self.url, response.status)
                    logger.error(result)
                    raise Exception("PATCH %s Status Code %d" % (self.url, response.status))

                return result
