from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class UserinfoRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, access_token=None):  # noqa: E501
        """UserinfoRequest - a model defined in OpenAPI

        :param access_token: The access_token of this UserinfoRequest.  # noqa: E501
        :type access_token: str
        """
        self.openapi_types = {
            'access_token': str
        }

        self.attribute_map = {
            'access_token': 'AccessToken'
        }

        self._access_token = access_token

    @classmethod
    def from_dict(cls, dikt) -> 'UserinfoRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The userinfo_request of this UserinfoRequest.  # noqa: E501
        :rtype: UserinfoRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def access_token(self) -> str:
        """Gets the access_token of this UserinfoRequest.


        :return: The access_token of this UserinfoRequest.
        :rtype: str
        """
        return self._access_token

    @access_token.setter
    def access_token(self, access_token: str):
        """Sets the access_token of this UserinfoRequest.


        :param access_token: The access_token of this UserinfoRequest.
        :type access_token: str
        """

        self._access_token = access_token
