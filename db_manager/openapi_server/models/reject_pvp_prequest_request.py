from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class RejectPvpPrequestRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, pvp_match_uuid=None, user_uuid=None):  # noqa: E501
        """RejectPvpPrequestRequest - a model defined in OpenAPI

        :param pvp_match_uuid: The pvp_match_uuid of this RejectPvpPrequestRequest.  # noqa: E501
        :type pvp_match_uuid: str
        :param user_uuid: The user_uuid of this RejectPvpPrequestRequest.  # noqa: E501
        :type user_uuid: str
        """
        self.openapi_types = {
            'pvp_match_uuid': str,
            'user_uuid': str
        }

        self.attribute_map = {
            'pvp_match_uuid': 'pvp_match_uuid',
            'user_uuid': 'user_uuid'
        }

        self._pvp_match_uuid = pvp_match_uuid
        self._user_uuid = user_uuid

    @classmethod
    def from_dict(cls, dikt) -> 'RejectPvpPrequestRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The reject_pvp_prequest_request of this RejectPvpPrequestRequest.  # noqa: E501
        :rtype: RejectPvpPrequestRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def pvp_match_uuid(self) -> str:
        """Gets the pvp_match_uuid of this RejectPvpPrequestRequest.

        UUID of the PvP match.  # noqa: E501

        :return: The pvp_match_uuid of this RejectPvpPrequestRequest.
        :rtype: str
        """
        return self._pvp_match_uuid

    @pvp_match_uuid.setter
    def pvp_match_uuid(self, pvp_match_uuid: str):
        """Sets the pvp_match_uuid of this RejectPvpPrequestRequest.

        UUID of the PvP match.  # noqa: E501

        :param pvp_match_uuid: The pvp_match_uuid of this RejectPvpPrequestRequest.
        :type pvp_match_uuid: str
        """

        self._pvp_match_uuid = pvp_match_uuid

    @property
    def user_uuid(self) -> str:
        """Gets the user_uuid of this RejectPvpPrequestRequest.

        UUID of user.  # noqa: E501

        :return: The user_uuid of this RejectPvpPrequestRequest.
        :rtype: str
        """
        return self._user_uuid

    @user_uuid.setter
    def user_uuid(self, user_uuid: str):
        """Sets the user_uuid of this RejectPvpPrequestRequest.

        UUID of user.  # noqa: E501

        :param user_uuid: The user_uuid of this RejectPvpPrequestRequest.
        :type user_uuid: str
        """

        self._user_uuid = user_uuid