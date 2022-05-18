from setuptools import setup, find_packages

setup(
    name = "sendlog",
    version = "0.3.1",
    description = "Tail log files and transmit to an RFC5424 syslog server",
    license = 'MIT',
    url = "https://github.com/nla/jvmctl",
    packages = ["sendlog"],
    test_suite = "tests",
    entry_points = {
        'console_scripts': [
            'sendlog=sendlog.main:main',
        ],
    },
    data_files = [
    ],
    install_requires = [
        'python-dateutil'
    ]
)
