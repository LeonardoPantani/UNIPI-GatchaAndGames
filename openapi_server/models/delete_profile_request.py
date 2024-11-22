from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class DeleteProfileRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, password=None):  # noqa: E501
        """DeleteProfileRequest - a model defined in OpenAPI

        :param password: The password of this DeleteProfileRequest.  # noqa: E501
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
    def from_dict(cls, dikt) -> 'DeleteProfileRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The deleteProfile_request of this DeleteProfileRequest.  # noqa: E501
        :rtype: DeleteProfileRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def password(self) -> str:
        """Gets the password of this DeleteProfileRequest.


        :return: The password of this DeleteProfileRequest.
        :rtype: str
        """
        return self._password

    @password.setter
    def password(self, password: str):
        """Sets the password of this DeleteProfileRequest.


        :param password: The password of this DeleteProfileRequest.
        :type password: str
        """

        self._password = password