from setuptools import setup, find_packages

setup(
    name = "logduct",
    version = "0.1.0",
    description = "Yet another logging daemon",
    license = 'MIT',
    url = "https://github.com/nla/jvmctl",
    packages = find_packages(exclude=['build', 'dist']),
    entry_points = {
      'console_scripts': [
        'logductd=logduct.daemon:main',
        'logduct-run=logduct.run:main',
      ],
    },
)
