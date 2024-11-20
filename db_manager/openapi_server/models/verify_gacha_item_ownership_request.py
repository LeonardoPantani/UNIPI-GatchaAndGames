from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
import re
from openapi_server import util

import re  # noqa: E501

class VerifyGachaItemOwnershipRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, team=None):  # noqa: E501
        """VerifyGachaItemOwnershipRequest - a model defined in OpenAPI

        :param team: The team of this VerifyGachaItemOwnershipRequest.  # noqa: E501
        :type team: str
        """
        self.openapi_types = {
            'team': str
        }

        self.attribute_map = {
            'team': 'team'
        }

        self._team = team

    @classmethod
    def from_dict(cls, dikt) -> 'VerifyGachaItemOwnershipRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The verify_gacha_item_ownership_request of this VerifyGachaItemOwnershipRequest.  # noqa: E501
        :rtype: VerifyGachaItemOwnershipRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def team(self) -> str:
        """Gets the team of this VerifyGachaItemOwnershipRequest.

        List (surrounded by round brackets) of gacha uuids separated by a comma  # noqa: E501

        :return: The team of this VerifyGachaItemOwnershipRequest.
        :rtype: str
        """
        return self._team

    @team.setter
    def team(self, team: str):
        """Sets the team of this VerifyGachaItemOwnershipRequest.

        List (surrounded by round brackets) of gacha uuids separated by a comma  # noqa: E501

        :param team: The team of this VerifyGachaItemOwnershipRequest.
        :type team: str
        """
        if team is not None and not re.search(r'^\(\s*[a-zA-Z]+\s*(,\s*[a-zA-Z]+\s*){6}\)$', team):  # noqa: E501
            raise ValueError("Invalid value for `team`.")  # noqa: E501

        self._team = team
