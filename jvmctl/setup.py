from setuptools import setup, find_packages
from setuptools.command.install import install

import site
import os
import glob

_name = "jvmctl"
with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as version_file:
    _version = version_file.read().strip()

setup(
    name = _name,
    version = _version,
    maintainer = "XXXNAME",
    maintainer_email = "XXXUSER@nla.gov.au",
    description = "Deploy and manage Java applications on RHEL servers",
    long_description = "Deploy and manage Java applications on RHEL servers",
    license = 'MIT',
    url = "https://github.com/nla/jvmctl",
    packages = find_packages(), #["jvmctl"],
    test_suite = "tests",
    entry_points = {
        'console_scripts': [
            'jvmctl=jvmctl.jvmctl:main',
            'hsperf=jvmctl.hsperf:main',
      ],
    },
    data_files = [
     ("/etc/bash_completion.d", ["bash_completion/jvmctl"]),
     ("/etc/jvmctl", []),
     ("/etc/jvmctl/apps", []),
     ("/logs", []),
     ("/apps", [])
    ]
)

