from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetGachaListRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, user_uuid=None, owned_filter=None):  # noqa: E501
        """GetGachaListRequest - a model defined in OpenAPI

        :param user_uuid: The user_uuid of this GetGachaListRequest.  # noqa: E501
        :type user_uuid: str
        :param owned_filter: The owned_filter of this GetGachaListRequest.  # noqa: E501
        :type owned_filter: bool
        """
        self.openapi_types = {
            'user_uuid': str,
            'owned_filter': bool
        }

        self.attribute_map = {
            'user_uuid': 'user_uuid',
            'owned_filter': 'owned_filter'
        }

        self._user_uuid = user_uuid
        self._owned_filter = owned_filter

    @classmethod
    def from_dict(cls, dikt) -> 'GetGachaListRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_gacha_list_request of this GetGachaListRequest.  # noqa: E501
        :rtype: GetGachaListRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def user_uuid(self) -> str:
        """Gets the user_uuid of this GetGachaListRequest.

        UUID of user.  # noqa: E501

        :return: The user_uuid of this GetGachaListRequest.
        :rtype: str
        """
        return self._user_uuid

    @user_uuid.setter
    def user_uuid(self, user_uuid: str):
        """Sets the user_uuid of this GetGachaListRequest.

        UUID of user.  # noqa: E501

        :param user_uuid: The user_uuid of this GetGachaListRequest.
        :type user_uuid: str
        """

        self._user_uuid = user_uuid

    @property
    def owned_filter(self) -> bool:
        """Gets the owned_filter of this GetGachaListRequest.

        Filters item list based on user ownership.  # noqa: E501

        :return: The owned_filter of this GetGachaListRequest.
        :rtype: bool
        """
        return self._owned_filter

    @owned_filter.setter
    def owned_filter(self, owned_filter: bool):
        """Sets the owned_filter of this GetGachaListRequest.

        Filters item list based on user ownership.  # noqa: E501

        :param owned_filter: The owned_filter of this GetGachaListRequest.
        :type owned_filter: bool
        """

        self._owned_filter = owned_filter
