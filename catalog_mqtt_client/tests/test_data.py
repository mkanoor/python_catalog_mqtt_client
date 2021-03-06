""" Test Data """
import configparser


class TestData:
    """ Test Data """

    config = configparser.ConfigParser()
    config["AUTH"] = {"x_rh_identity": "123", "username": "fred", "password": "secret", "verify_ssl": "True"}
    config["ANSIBLE_TOWER"] = {
        "url": "https://www.example.com",
        "token": "chucky_cheese",
        "verify_ssl": "True",
    }
    no_verify_config = configparser.ConfigParser()
    no_verify_config["AUTH"] = {
        "x_rh_identity": "123",
        "username": "fred",
        "password": "secret",
        "verify_ssl": "False",
    }
    no_verify_config["ANSIBLE_TOWER"] = {
        "url": "https://www.example.com",
        "token": "chucky_cheese",
        "verify_ssl": "False",
    }

    JOB_TEMPLATE_ID_1 = 909
    JOB_TEMPLATE_ID_2 = 910
    JOB_TEMPLATE_ID_3 = 987
    ARTIFACTS_KEY_PREFIX = "expose_to_cloud_redhat_com_"

    DEFAULT_JOB_TEMPLATES_LIST_URL = "https://www.example.com/api/v2/job_templates"
    JOB_TEMPLATES_LIST_URL = "https://www.example.com/api/v2/job_templates?page_size=2"
    JOB_TEMPLATES_LIST_URL_PAGE_2 = (
        "https://www.example.com/api/v2/job_templates?page=2&page_size=2"
    )
    SURVEY_URL = (
        f"https://www.example.com/api/v2/job_templates/{JOB_TEMPLATE_ID_1}/survey_spec"
    )
    JOB_TEMPLATE_ID_1_URL = (
        f"https://www.example.com/api/v2/job_templates/{JOB_TEMPLATE_ID_1}"
    )
    SURVEY_DATA = dict(name="fred", description="test", spec=[])

    JOB_TEMPLATE_PAYLOAD_SINGLE_RELATED = dict(
        href_slug=f"api/v2/job_templates/{JOB_TEMPLATE_ID_1}",
        method="get",
        fetch_all_pages="False",
        page_prefix="my_prefix",
        fetch_related=[dict(predicate="survey_spec", href_slug="survey_url")],
    )
    JOB_TEMPLATE_PAYLOAD_FETCH_RELATED = dict(
        href_slug="api/v2/job_templates",
        method="get",
        fetch_all_pages="False",
        params=dict(page_size=1),
        page_prefix="my_prefix",
        fetch_related=[dict(predicate="survey_spec", href_slug="survey_url")],
    )
    JOB_TEMPLATE_PAYLOAD_SINGLE_PAGE = dict(
        href_slug="api/v2/job_templates",
        method="get",
        fetch_all_pages="False",
        params=dict(page_size=1),
        page_prefix="my_prefix",
    )
    JOB_TEMPLATE_PAYLOAD_ALL_PAGES = dict(
        href_slug="api/v2/job_templates?page_size=2",
        method="get",
        fetch_all_pages="True",
        apply_filter="results[].{id:id,name:name}",
    )
    JOB_TEMPLATE_COUNT = 3
    JOB_TEMPLATE_1 = dict(
        # Survey URL needs to have a leading slash
        id=JOB_TEMPLATE_ID_1,
        type="job_template",
        name="Fred Flintstone",
        survey_spec=True,
        survey_url=f"/api/v2/job_templates/{JOB_TEMPLATE_ID_1}/survey_spec",
    )
    JOB_TEMPLATE_2 = dict(
        id=JOB_TEMPLATE_ID_2, type="job_template", name="Pebbles Flintstone"
    )
    JOB_TEMPLATE_3 = dict(
        id=JOB_TEMPLATE_ID_3, type="job_template", name="Wilma Flintstone"
    )

    JOB_TEMPLATE_SINGLE_RESPONSE = JOB_TEMPLATE_1
    JOB_TEMPLATE_RESPONSE = dict(
        count=JOB_TEMPLATE_COUNT,
        next=None,
        previous=None,
        results=[JOB_TEMPLATE_1, JOB_TEMPLATE_2],
    )

    JOB_TEMPLATES_PAGE1_RESPONSE = dict(
        count=JOB_TEMPLATE_COUNT,
        next="/api/v2/job_templates/?page=2",
        previous=None,
        results=[JOB_TEMPLATE_1, JOB_TEMPLATE_2],
    )
    JOB_TEMPLATES_PAGE2_RESPONSE = dict(
        count=JOB_TEMPLATE_COUNT, next=None, previous=None, results=[JOB_TEMPLATE_3],
    )

    JOB_TEMPLATE_POST_URL = "https://www.example.com/api/v2/job_templates/909/launch"
    JOB_TEMPLATE_POST_PAYLOAD = dict(
        href_slug="api/v2/job_templates/909/launch",
        method="post",
        params=dict(name="Fred"),
    )

    INVALID_PAYLOAD = dict(href_slug="api/v2/job_templates/909/launch", method="bad",)
    JOB_ID_1 = 500
    JOB_STATUS_RUNNING = "running"
    JOB_STATUS_FAILED = "failed"
    JOB_STATUS_SUCCESSFUL = "successful"
    JOB_ARTIFACTS = {
        f"{ARTIFACTS_KEY_PREFIX}_snow_ticket": 12345,
        "fred": 45,
        "barney": 90,
    }
    JOB_ARTIFACTS_HUGE = {f"{ARTIFACTS_KEY_PREFIX}_snow_details": "f" * 1096}
    JOB_TEMPLATE_POST_RESPONSE = dict(
        job=JOB_ID_1,
        url=f"/api/v2/jobs/{JOB_ID_1}",
        playbook="hello_world.yml",
        status=JOB_STATUS_SUCCESSFUL,
        artifacts=JOB_ARTIFACTS,
    )
    FILTERED_JOB_ARTIFACTS = {f"{ARTIFACTS_KEY_PREFIX}_snow_ticket": 12345}
    JOB_1 = dict(
        job=JOB_ID_1,
        url=f"/api/v2/jobs/{JOB_ID_1}",
        playbook="hello_world.yml",
        status=JOB_STATUS_SUCCESSFUL,
        artifacts=FILTERED_JOB_ARTIFACTS,
    )
    JOB_1_RUNNING = dict(
        job=JOB_ID_1,
        url=f"/api/v2/jobs/{JOB_ID_1}",
        playbook="hello_world.yml",
        status=JOB_STATUS_RUNNING,
    )
    JOB_1_SUCCESSFUL = dict(
        job=JOB_ID_1,
        url=f"/api/v2/jobs/{JOB_ID_1}",
        playbook="hello_world.yml",
        status=JOB_STATUS_SUCCESSFUL,
        artifacts=JOB_ARTIFACTS,
    )
    JOB_1_SUCCESSFUL_HUGE = dict(
        job=JOB_ID_1,
        url=f"/api/v2/jobs/{JOB_ID_1}",
        playbook="hello_world.yml",
        status=JOB_STATUS_SUCCESSFUL,
        artifacts=JOB_ARTIFACTS_HUGE,
    )
    JOB_MONITOR_URL = f"https://www.example.com/api/v2/jobs/{JOB_ID_1}"
    JOB_FILTER = {
        "url": "url",
        "id": "id",
        "status": "status",
        "playbook": "playbook",
        "artifacts": "artifacts",
    }
    JOB_GET_PAYLOAD = dict(
        href_slug=f"/api/v2/jobs/{JOB_ID_1}",
        method="get",
        params={},
        apply_filter=JOB_FILTER,
    )
    JOB_MONITOR_PAYLOAD = dict(
        href_slug=f"/api/v2/jobs/{JOB_ID_1}",
        method="monitor",
        params={},
        refresh_interval_seconds=1,
        apply_filter=JOB_FILTER,
    )
    JOB_TEMPLATE_LAUNCH_PAYLOAD = dict(
        href_slug="api/v2/job_templates/909/launch",
        method="launch",
        params={},
        refresh_interval_seconds=1,
        apply_filter=JOB_FILTER,
    )
    UPLOAD_URL="http://www.example.com/upload/catalog"
