import sys
from setuptools import setup, find_packages

NAME = "openapi_server"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion>=2.0.2",
    "swagger-ui-bundle>=0.0.2",
    "python_dateutil>=2.6.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="Gacha System - OpenAPI 3.0",
    author_email="support@gachaandgames.it",
    url="",
    keywords=["OpenAPI", "Gacha System - OpenAPI 3.0"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['openapi_server=openapi_server.__main__:main']},
    long_description="""\
    API for managing gacha items, auctions, PVP battles, currency, and user authentication.  Useful links: - [Project repository](https://github.com/LeonardoPantani/UNIPI-GachaAndGames)
    """
)

