from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetHashedPassword200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, password=None):  # noqa: E501
        """GetHashedPassword200Response - a model defined in OpenAPI

        :param password: The password of this GetHashedPassword200Response.  # noqa: E501
        :type password: str
        """
        self.openapi_types = {
            'password': str
        }

        self.attribute_map = {
            'password': 'password'
        }

        self._password = password

    @classmethod
    def from_dict(cls, dikt) -> 'GetHashedPassword200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_hashed_password_200_response of this GetHashedPassword200Response.  # noqa: E501
        :rtype: GetHashedPassword200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def password(self) -> str:
        """Gets the password of this GetHashedPassword200Response.


        :return: The password of this GetHashedPassword200Response.
        :rtype: str
        """
        return self._password

    @password.setter
    def password(self, password: str):
        """Sets the password of this GetHashedPassword200Response.


        :param password: The password of this GetHashedPassword200Response.
        :type password: str
        """

        self._password = password
