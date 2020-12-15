""" Tower API Worker, makes REST API calls to the Tower """
import os
import json
import logging
import ssl
import asyncio
from urllib.parse import urlparse
from urllib.parse import parse_qsl
from urllib.parse import urljoin
from distutils.util import strtobool
import aiohttp
import jmespath

logger = logging.getLogger(__name__)


class TowerApiWorker:
    """ Tower API Worker, picks work items from a queue and dispatches API
        requests to the Tower. It writes the response to passed in writer
    """

    VALID_POST_CODES = [200, 201, 202]
    JOB_COMPLETION_STATUSES = ["successful", "failed", "error", "canceled"]
    DEFAULT_REFRESH_INTERVAL = 10
    ARTIFACTS_KEY_PREFIX = "expose_to_cloud_redhat_com_"
    MAX_ARTIFACTS_SIZE = 1024

    def __init__(self, config, writer, queue):
        self.writer = writer
        self.queue = queue
        self.config = config
        self.initialize_ssl()

    async def start(self):
        """ Make the API request based on the specified method
            It picks up one request at a time from the Queue. There
            could be multiple workers reading from the same queue
        """
        async with aiohttp.ClientSession(headers=self.auth_headers()) as session:
            while not self.queue.empty():
                job = await self.queue.get()
                logger.debug(job["method"] + ":" + job["href_slug"])
                if job["method"] == "get":
                    await self.get(session, job["href_slug"], job)
                elif job["method"] == "post":
                    await self.post(session, job["href_slug"], job)
                elif job["method"] == "launch":
                    await self.launch(session, job["href_slug"], job)
                elif job["method"] == "monitor":
                    await self.monitor(session, job["href_slug"], job)
                else:
                    raise Exception(f"Invalid method {job['method']}")

    async def get(self, session, href_slug, job):
        """ Send an HTTP Get request to the Ansible Tower API
            supports
            Fetching all pages from the end point using fetch_all_pages = True
            Fetch related objects
         """
        url_info = urlparse(href_slug)
        params = dict(parse_qsl(url_info.query))
        page_number = 1
        while True:
            response = await self.get_page(session, url_info.path, params)
            if response["status"] != 200:
                raise Exception(
                    "Get failed %s status %s body %s"
                    % (href_slug, response["status"], response.get("body", "empty"))
                )

            json_body = json.loads(response["body"])
            page_prefix = job.get("page_prefix", "page")

            page_name = os.path.join(url_info.path, page_prefix + str(page_number))
            await self.send_response(json_body, page_name, job)

            if job.get("fetch_all_pages", False):
                page_number = page_number + 1
                if json_body.get("next", None):
                    params["page"] = params.get("page", 1) + 1
                else:
                    break
            else:
                break

    async def post(self, session, href_slug, job):
        """ Post the data to the Ansible Tower """
        url = urljoin(self.config["ANSIBLE_TOWER"]["url"], href_slug)
        async with session.post(
            url, json=job["params"], ssl=self.ssl_context
        ) as post_response:
            response = dict(
                status=post_response.status, body=await post_response.text()
            )

            if response["status"] not in self.VALID_POST_CODES:
                raise Exception(
                    "Post failed %s status %s body %s"
                    % (url, response["status"], response.get("body", "empty"))
                )

            await self.send_response(json.loads(response["body"]), url, job)

    async def launch(self, session, href_slug, job):
        """ Post the data to the Ansible Tower and then monitor for completion """
        url = urljoin(self.config["ANSIBLE_TOWER"]["url"], href_slug)
        async with session.post(
            url, json=job["params"], ssl=self.ssl_context
        ) as post_response:
            response = dict(
                status=post_response.status, body=await post_response.text()
            )

            if response["status"] not in self.VALID_POST_CODES:
                raise Exception(
                    "Post failed %s status %s body %s"
                    % (url, response["status"], response.get("body", "empty"))
                )
            json_body = json.loads(response["body"])
            await self.send_response(json_body, url, job)
            new_job = {
                "href_slug": json_body["url"],
                "method": "monitor",
                "apply_filter": job["apply_filter"],
                "refresh_interval_seconds": job.get(
                    "refresh_interval_seconds", self.DEFAULT_REFRESH_INTERVAL
                ),
            }
            await self.queue.put(new_job)

    async def add_related(self, json_body, job):
        """ Add related objects to the work queue so we can fetch them """

        if "fetch_related" in job:
            if "results" in json_body:
                for obj in json_body["results"]:
                    await self.add_related_to_queue(obj, job["fetch_related"])
            else:
                await self.add_related_to_queue(json_body, job["fetch_related"])

    async def add_related_to_queue(self, obj, related):
        """ Fetch any related objects by checking the predicate
            and adding it to the work queue. A good example of this is
            the survey_spec which is optional for job_template and worklow_job_templates
            If the survey_enabled is true (the predicate) we will add the URL to the
            queue so we can retrieve it
        """
        for rel in related:
            key = rel["predicate"]
            val = rel["href_slug"]
            logger.debug(obj)
            if obj.get(key, None):
                new_job = {"href_slug": obj[val][1:], "method": "get"}
                logger.debug(new_job)
                await self.queue.put(new_job)

    async def get_page(self, session, href_slug, params):
        """ Get a single page from the Tower API """
        url = urljoin(self.config["ANSIBLE_TOWER"]["url"], href_slug)
        async with session.get(url, params=params, ssl=self.ssl_context) as response:
            response_text = dict(status=response.status, body=await response.text())
        return response_text

    def filter_artifacts(self, json_body):
        """ To prevent exposure of all attributes in the artifacts from the
            job, we only expose ones with a specific prefix
        """
        artifacts = {}
        for key in json_body["artifacts"]:
            if key.startswith(self.ARTIFACTS_KEY_PREFIX):
                artifacts[key] = json_body["artifacts"][key]

        if len(json.dumps(artifacts)) > self.MAX_ARTIFACTS_SIZE:
            raise Exception(f"Artifacts is over {self.MAX_ARTIFACTS_SIZE} bytes")

        json_body["artifacts"] = artifacts
        return json_body

    def auth_headers(self):
        """ Create proper authentication headers based on Token """
        headers = {}
        headers["Authorization"] = "Bearer " + self.config["ANSIBLE_TOWER"]["token"]
        return headers

    async def monitor(self, session, url, job):
        """ Monitor a Ansible Tower Job """
        url_info = urlparse(url)
        params = dict(parse_qsl(url_info.query))
        while True:
            response = await self.get_page(session, url_info.path, params)
            if response["status"] != 200:
                raise Exception(
                    "GET failed %s status %s body %s"
                    % (url, response["status"], response.get("body", "empty"))
                )

            json_body = json.loads(response["body"])
            if json_body["status"] not in self.JOB_COMPLETION_STATUSES:
                await asyncio.sleep(
                    job.get("refresh_interval_seconds", self.DEFAULT_REFRESH_INTERVAL)
                )
                continue

            await self.send_response(json_body, url, job)
            break

    async def send_response(self, json_body, name, job):
        """ Send the response to the writer, which would send it
            via the appropriate route (upload to ingress service)
            or directly update the task result
        """
        if "apply_filter" in job:
            json_body = filter_body(job["apply_filter"], json_body)

        if isinstance(json_body, dict) and isinstance(
            json_body.get("artifacts", None), dict
        ):
            json_body = self.filter_artifacts(json_body)

        await self.add_related(json_body, job)
        await self.writer.write(json.dumps(json_body), name)

    def initialize_ssl(self):
        """ Configure SSL for the current session """
        self.ssl_context = ssl.SSLContext()
        # if self.config.get('ca_file', None):
        #    self.ssl_context.load_verify_locations(ca_file=self.config['ca_file'])
        verify_ssl = self.config["ANSIBLE_TOWER"]["verify_ssl"]
        if isinstance(verify_ssl, str):
            verify_ssl = strtobool(verify_ssl)

        if not verify_ssl:
            self.ssl_context.verify_mode = ssl.CERT_NONE


# Local Function to apply JMES Path Filter
def filter_body(apply_filters, json_body):
    """ Apply JMESPath filters to the json body"""
    if isinstance(apply_filters, dict):
        new_data = {}
        for key, jmes_filter in apply_filters.items():
            new_data[key] = jmespath.search(jmes_filter, json_body)
        json_body = new_data
    elif isinstance(apply_filters, str):
        json_body["results"] = jmespath.search(apply_filters, json_body)

    return json_body
