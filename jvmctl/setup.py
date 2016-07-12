from setuptools import setup, find_packages

setup(
    name = "jvmctl",
    version = "0.2.0",
    description = "Deploying and manage Java applications on EL7 servers",
    license = 'MIT',
    url = "https://github.com/nla/jvmctl",
    packages = ["jvmctl"],
    test_suite = "tests",
    entry_points = {
        'console_scripts': [
            'jvmctl=jvmctl.jvmctl:main',
            'hsperf=jvmctl.hsperf:main',
      ],
    },
)
