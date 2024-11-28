from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server.models.team import Team
from openapi_server import util

from openapi_server.models.team import Team  # noqa: E501

class CheckOwnerOfTeamRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, team=None):  # noqa: E501
        """CheckOwnerOfTeamRequest - a model defined in OpenAPI

        :param team: The team of this CheckOwnerOfTeamRequest.  # noqa: E501
        :type team: Team
        """
        self.openapi_types = {
            'team': Team
        }

        self.attribute_map = {
            'team': 'team'
        }

        self._team = team

    @classmethod
    def from_dict(cls, dikt) -> 'CheckOwnerOfTeamRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The check_owner_of_team_request of this CheckOwnerOfTeamRequest.  # noqa: E501
        :rtype: CheckOwnerOfTeamRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def team(self) -> Team:
        """Gets the team of this CheckOwnerOfTeamRequest.


        :return: The team of this CheckOwnerOfTeamRequest.
        :rtype: Team
        """
        return self._team

    @team.setter
    def team(self, team: Team):
        """Sets the team of this CheckOwnerOfTeamRequest.


        :param team: The team of this CheckOwnerOfTeamRequest.
        :type team: Team
        """

        self._team = team
