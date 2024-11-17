from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
import re
from openapi_server import util

import re  # noqa: E501

class LoginRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, username=None, password=None):  # noqa: E501
        """LoginRequest - a model defined in OpenAPI

        :param username: The username of this LoginRequest.  # noqa: E501
        :type username: str
        :param password: The password of this LoginRequest.  # noqa: E501
        :type password: str
        """
        self.openapi_types = {
            'username': str,
            'password': str
        }

        self.attribute_map = {
            'username': 'username',
            'password': 'password'
        }

        self._username = username
        self._password = password

    @classmethod
    def from_dict(cls, dikt) -> 'LoginRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The login_request of this LoginRequest.  # noqa: E501
        :rtype: LoginRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def username(self) -> str:
        """Gets the username of this LoginRequest.

        The username of the user  # noqa: E501

        :return: The username of this LoginRequest.
        :rtype: str
        """
        return self._username

    @username.setter
    def username(self, username: str):
        """Sets the username of this LoginRequest.

        The username of the user  # noqa: E501

        :param username: The username of this LoginRequest.
        :type username: str
        """
        if username is not None and len(username) < 5:
            raise ValueError("Invalid value for `username`, length must be greater than or equal to `5`")  # noqa: E501
        if username is not None and not re.search(r'^[a-zA-Z0-9_]+$', username):  # noqa: E501
            raise ValueError("Invalid value for `username`, must be a follow pattern or equal to `/^[a-zA-Z0-9_]+$/`")  # noqa: E501

        self._username = username

    @property
    def password(self) -> str:
        """Gets the password of this LoginRequest.

        User's password  # noqa: E501

        :return: The password of this LoginRequest.
        :rtype: str
        """
        return self._password

    @password.setter
    def password(self, password: str):
        """Sets the password of this LoginRequest.

        User's password  # noqa: E501

        :param password: The password of this LoginRequest.
        :type password: str
        """

        self._password = password
