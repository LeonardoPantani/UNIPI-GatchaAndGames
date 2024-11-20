from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetPvpStatusRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, pvp_match_uuid=None):  # noqa: E501
        """GetPvpStatusRequest - a model defined in OpenAPI

        :param pvp_match_uuid: The pvp_match_uuid of this GetPvpStatusRequest.  # noqa: E501
        :type pvp_match_uuid: str
        """
        self.openapi_types = {
            'pvp_match_uuid': str
        }

        self.attribute_map = {
            'pvp_match_uuid': 'pvp_match_uuid'
        }

        self._pvp_match_uuid = pvp_match_uuid

    @classmethod
    def from_dict(cls, dikt) -> 'GetPvpStatusRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_pvp_status_request of this GetPvpStatusRequest.  # noqa: E501
        :rtype: GetPvpStatusRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def pvp_match_uuid(self) -> str:
        """Gets the pvp_match_uuid of this GetPvpStatusRequest.

        UUID of the PvP match.  # noqa: E501

        :return: The pvp_match_uuid of this GetPvpStatusRequest.
        :rtype: str
        """
        return self._pvp_match_uuid

    @pvp_match_uuid.setter
    def pvp_match_uuid(self, pvp_match_uuid: str):
        """Sets the pvp_match_uuid of this GetPvpStatusRequest.

        UUID of the PvP match.  # noqa: E501

        :param pvp_match_uuid: The pvp_match_uuid of this GetPvpStatusRequest.
        :type pvp_match_uuid: str
        """

        self._pvp_match_uuid = pvp_match_uuid
