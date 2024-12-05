from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class PendingPvPRequestsInner(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, pvp_match_id=None, _from=None):  # noqa: E501
        """PendingPvPRequestsInner - a model defined in OpenAPI

        :param pvp_match_id: The pvp_match_id of this PendingPvPRequestsInner.  # noqa: E501
        :type pvp_match_id: str
        :param _from: The _from of this PendingPvPRequestsInner.  # noqa: E501
        :type _from: str
        """
        self.openapi_types = {
            'pvp_match_id': str,
            '_from': str
        }

        self.attribute_map = {
            'pvp_match_id': 'pvp_match_id',
            '_from': 'from'
        }

        self._pvp_match_id = pvp_match_id
        self.__from = _from

    @classmethod
    def from_dict(cls, dikt) -> 'PendingPvPRequestsInner':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The PendingPvPRequests_inner of this PendingPvPRequestsInner.  # noqa: E501
        :rtype: PendingPvPRequestsInner
        """
        return util.deserialize_model(dikt, cls)

    @property
    def pvp_match_id(self) -> str:
        """Gets the pvp_match_id of this PendingPvPRequestsInner.

        UUID of the PvP match.  # noqa: E501

        :return: The pvp_match_id of this PendingPvPRequestsInner.
        :rtype: str
        """
        return self._pvp_match_id

    @pvp_match_id.setter
    def pvp_match_id(self, pvp_match_id: str):
        """Sets the pvp_match_id of this PendingPvPRequestsInner.

        UUID of the PvP match.  # noqa: E501

        :param pvp_match_id: The pvp_match_id of this PendingPvPRequestsInner.
        :type pvp_match_id: str
        """

        self._pvp_match_id = pvp_match_id

    @property
    def _from(self) -> str:
        """Gets the _from of this PendingPvPRequestsInner.

        UUID of user.  # noqa: E501

        :return: The _from of this PendingPvPRequestsInner.
        :rtype: str
        """
        return self.__from

    @_from.setter
    def _from(self, _from: str):
        """Sets the _from of this PendingPvPRequestsInner.

        UUID of user.  # noqa: E501

        :param _from: The _from of this PendingPvPRequestsInner.
        :type _from: str
        """

        self.__from = _from