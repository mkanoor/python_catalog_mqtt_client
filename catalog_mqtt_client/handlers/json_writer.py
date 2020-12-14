""" JSON Writer, writes JSON back to the cloud """
import json
import logging

logger = logging.getLogger(__name__)


class JSONWriter:
    """ JSON Writer Class, supports write/flush/flush_errors/cleanup methods """

    def __init__(self, config, c_task):
        self.config = config
        self.c_task = c_task

    async def write(self, data, filename):
        """ Write a Page to the Catalog Task in the cloud"""
        logger.debug("JSON Page %s", filename)
        await self.c_task.update(
            {"output": json.loads(data), "state": "running", "status": "ok"}
        )

    async def flush(self):
        """ Flush the final data to  Catalog Task in the cloud"""
        data = {"state": "completed", "status": "ok"}
        await self.c_task.update(data)

    async def flush_errors(self, errors):
        """ Flush the errors to  Catalog Task in the cloud"""
        logger.error(errors)
        data = {"output": {"errors": errors}, "state": "completed", "status": "error"}
        await self.c_task.update(data)

    # pylint: disable=W0107
    # This dummy function is needed to satisfy the interface definition for writer
    # for JSON we dont have any cleanup but for the TarWriter we have to remove the
    # Temporary Directory and delete the temporary tgz file
    def cleanup(self):
        """ Cleanup function """
        pass
