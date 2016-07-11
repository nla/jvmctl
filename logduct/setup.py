from setuptools import setup, find_packages

setup(
    name = "logduct",
    version = "0.1.1",
    description = "Yet another logging daemon",
    license = 'MIT',
    url = "https://github.com/nla/jvmctl",
    packages = ["logduct"],
    test_suite = "tests",
    entry_points = {
        'console_scripts': [
            'logductd=logduct.daemon:main',
            'logduct-run=logduct.run:main',
      ],
    },
    data_files = [
        ("/usr/lib/systemd/system/", ["systemd/logductd.service", "systemd/logductd.socket"]),
    ],
)
