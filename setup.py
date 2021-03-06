#!/usr/bin/env python3

"""
Packaging and installation for the apssh package
"""

import setuptools

# https://packaging.python.org/guides/single-sourcing-package-version/
# set __version__ by read & exec of the python code
# this is better than an import that would otherwise try to
# import the whole package, and fail if a required module is not yet there
from pathlib import Path
VERSION_FILE = Path(__file__).parent / "apssh" / "version.py"
ENV = {}
with VERSION_FILE.open() as f:
    exec(f.read(), ENV)
__version__ = ENV['__version__']

LONG_DESCRIPTION = \
    "See README at https://github.com/parmentelat/apssh/blob/master/README.md"

# requirements - used by pip install
# *NOTE* for ubuntu, to install asyncssh, at some point in time_ok
# there has been a need to also run this beforehand:
# apt-get -y install libffi-dev libssl-dev
# which is required before pip can install asyncssh
REQUIRED_MODULES = [
    'asyncssh',
    'asynciojobs',
]

setuptools.setup(
    name="apssh",
    author="Thierry Parmentelat",
    author_email="thierry.parmentelat@inria.fr",
    description="Asynchroneous Parallel ssh",
    long_description=LONG_DESCRIPTION,
    license="CC BY-SA 4.0",
    keywords=['asyncio', 'remote shell', 'parallel ssh'],

    packages=['apssh'],
    version=__version__,
    python_requires=">=3.5",

    entry_points={
        'console_scripts': [
            'apssh = apssh.__main__:main'
        ]
    },

    install_requires=REQUIRED_MODULES,

    project_urls={
        'source': 'http://github.com/parmentelat/apssh',
        'documentation': 'http://apssh.readthedocs.io/',
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3.5",
    ],
)
