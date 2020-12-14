""" Tar Writer, writes pages to a temporary directory and when
    its time to flush the response to the cloud, it creates a
    tar file and uploads it to the ingress service. Once it has
    uploaded the file, it updates the Catalog Task Object
"""
import tempfile
from distutils.util import strtobool
import tarfile
import os
import ssl
import json
import shutil
import logging
import aiohttp

logger = logging.getLogger(__name__)


class TarWriter:
    """ Tar Writer supports write/flush/flush_errors methods """

    UPLOAD_CONTENT_TYPE = "application/vnd.redhat.topological-inventory.filename+tgz"

    def __init__(self, config, c_task, upload_url):
        self.config = config
        self.upload_url = upload_url
        self.c_task = c_task
        self.dirname = tempfile.TemporaryDirectory(prefix="catalog").name
        self.tgzfile = tempfile.NamedTemporaryFile(prefix="catalog", suffix=".tgz").name
        self.initialize_ssl()

    async def write(self, data, filename):
        """ Write a file to the temporary directory """
        logger.debug("JSON Page %s", filename)
        fullpath = os.path.join(self.dirname, filename)
        basedir = os.path.dirname(fullpath)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        with open(fullpath, "w") as file_handle:
            file_handle.write(data)

    async def flush(self):
        """ Compress all the files into a tarfile and send it to the ingress service"""
        self.create_tar()
        logger.debug("Tar file is %s", self.tgzfile)
        result = await self.upload_file()
        data = {"output": json.loads(result), "state": "completed", "status": "ok"}
        await self.c_task.update(data)

    async def flush_errors(self, errors):
        """ If we encountered any errors, flush all the errors to the cloud task"""
        logger.error(errors)
        data = {"output": {"errors": errors}, "state": "completed", "status": "error"}
        await self.c_task.update(data)

    def create_tar(self):
        """ Create a tar file in a temporary file """
        with tarfile.open(self.tgzfile, "w:gz") as tar_handle:
            for root, _, files in os.walk(self.dirname):
                for file in files:
                    tar_handle.add(os.path.join(root, file))

    async def upload_file(self):
        """ Upload the tarfile to cloud as multipart data"""
        logger.debug("uploading %s", self.tgzfile)
        with aiohttp.MultipartWriter("form-data") as mpwriter:
            with open(self.tgzfile, "rb") as file_handle:
                part = mpwriter.append(file_handle)
                part.set_content_disposition(
                    "form-data", name="file", filename="inventory.gz"
                )
                part.headers[aiohttp.hdrs.CONTENT_TYPE] = self.UPLOAD_CONTENT_TYPE

                headers = {}
                # TODO : Use mTLS certs not userid/password
                auth = aiohttp.BasicAuth(
                    self.config["AUTH"]["username"], self.config["AUTH"]["password"]
                )
                headers["Authorization"] = auth.encode()
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.post(
                        self.upload_url, ssl=self.ssl_context, data=mpwriter
                    ) as response:
                        logger.debug("Status: %s", response.status)
                        logger.debug(
                            "Content-type: %s", response.headers["Content-Type"]
                        )

                        return await response.text()

    def initialize_ssl(self):
        """ Configure SSL for the current session """
        self.ssl_context = ssl.SSLContext()
        # if self.config.get('ca_file', None):
        #    self.ssl_context.load_verify_locations(ca_file=self.config['ca_file'])

        # TODO : Remove this

        verify_ssl = self.config["AUTH"]["verify_ssl"]
        if isinstance(verify_ssl, str):
            verify_ssl = strtobool(verify_ssl)

        if not verify_ssl:
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def cleanup(self):
        """ Clean the Temporary directory where we were collecting the files """
        os.remove(self.tgzfile)
        shutil.rmtree(self.dirname)
