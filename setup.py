#!/usr/bin/env python

# Copyright (c) 2020 Red Hat, Inc.
# All Rights Reserved.

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="catalog-mqtt-client",
    version="0.0.1",
    author="Red Hat Insights",
    author_email="support@redhat.com",
    url="https://github.com/mkanoor/python_catalog_mqtt_client",
    license="Apache",
    packages=find_packages(),
    description="Catalog MQTT client to communicate with Ansible Tower API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["paho-mqtt", "aiohttp", "jmespath"],
    tests_require=["pytest-asyncio","aioresponses","pytest"],
    zip_safe=False,
    classifiers=["Programming Language :: Python :: 3"],
    extras_require={"dev": ["pytest", "flake8", "pylint", "black"]},
)
