from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class RegisterRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, username=None, email=None, password=None):  # noqa: E501
        """RegisterRequest - a model defined in OpenAPI

        :param username: The username of this RegisterRequest.  # noqa: E501
        :type username: str
        :param email: The email of this RegisterRequest.  # noqa: E501
        :type email: str
        :param password: The password of this RegisterRequest.  # noqa: E501
        :type password: str
        """
        self.openapi_types = {
            'username': str,
            'email': str,
            'password': str
        }

        self.attribute_map = {
            'username': 'username',
            'email': 'email',
            'password': 'password'
        }

        self._username = username
        self._email = email
        self._password = password

    @classmethod
    def from_dict(cls, dikt) -> 'RegisterRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The register_request of this RegisterRequest.  # noqa: E501
        :rtype: RegisterRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def username(self) -> str:
        """Gets the username of this RegisterRequest.

        The user's username. Must be at least 5 characters long and contain only letters, numbers, and underscores.  # noqa: E501

        :return: The username of this RegisterRequest.
        :rtype: str
        """
        return self._username

    @username.setter
    def username(self, username: str):
        """Sets the username of this RegisterRequest.

        The user's username. Must be at least 5 characters long and contain only letters, numbers, and underscores.  # noqa: E501

        :param username: The username of this RegisterRequest.
        :type username: str
        """
        if username is None:
            raise ValueError("Invalid value for `username`, must not be `None`")  # noqa: E501

        self._username = username

    @property
    def email(self) -> str:
        """Gets the email of this RegisterRequest.

        The user's email address. Must be a valid email format.  # noqa: E501

        :return: The email of this RegisterRequest.
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, email: str):
        """Sets the email of this RegisterRequest.

        The user's email address. Must be a valid email format.  # noqa: E501

        :param email: The email of this RegisterRequest.
        :type email: str
        """
        if email is None:
            raise ValueError("Invalid value for `email`, must not be `None`")  # noqa: E501

        self._email = email

    @property
    def password(self) -> str:
        """Gets the password of this RegisterRequest.

        The user's password.  # noqa: E501

        :return: The password of this RegisterRequest.
        :rtype: str
        """
        return self._password

    @password.setter
    def password(self, password: str):
        """Sets the password of this RegisterRequest.

        The user's password.  # noqa: E501

        :param password: The password of this RegisterRequest.
        :type password: str
        """
        if password is None:
            raise ValueError("Invalid value for `password`, must not be `None`")  # noqa: E501

        self._password = password
