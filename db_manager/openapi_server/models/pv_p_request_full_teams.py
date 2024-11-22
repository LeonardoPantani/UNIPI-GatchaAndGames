from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class PvPRequestFullTeams(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, team1=None, team2=None):  # noqa: E501
        """PvPRequestFullTeams - a model defined in OpenAPI

        :param team1: The team1 of this PvPRequestFullTeams.  # noqa: E501
        :type team1: List[str]
        :param team2: The team2 of this PvPRequestFullTeams.  # noqa: E501
        :type team2: List[str]
        """
        self.openapi_types = {
            'team1': List[str],
            'team2': List[str]
        }

        self.attribute_map = {
            'team1': 'team1',
            'team2': 'team2'
        }

        self._team1 = team1
        self._team2 = team2

    @classmethod
    def from_dict(cls, dikt) -> 'PvPRequestFullTeams':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The PvPRequestFull_teams of this PvPRequestFullTeams.  # noqa: E501
        :rtype: PvPRequestFullTeams
        """
        return util.deserialize_model(dikt, cls)

    @property
    def team1(self) -> List[str]:
        """Gets the team1 of this PvPRequestFullTeams.

        Team used by players to battle each others.  # noqa: E501

        :return: The team1 of this PvPRequestFullTeams.
        :rtype: List[str]
        """
        return self._team1

    @team1.setter
    def team1(self, team1: List[str]):
        """Sets the team1 of this PvPRequestFullTeams.

        Team used by players to battle each others.  # noqa: E501

        :param team1: The team1 of this PvPRequestFullTeams.
        :type team1: List[str]
        """
        if team1 is not None and len(team1) > 7:
            raise ValueError("Invalid value for `team1`, number of items must be less than or equal to `7`")  # noqa: E501
        if team1 is not None and len(team1) < 7:
            raise ValueError("Invalid value for `team1`, number of items must be greater than or equal to `7`")  # noqa: E501

        self._team1 = team1

    @property
    def team2(self) -> List[str]:
        """Gets the team2 of this PvPRequestFullTeams.

        Team used by players to battle each others.  # noqa: E501

        :return: The team2 of this PvPRequestFullTeams.
        :rtype: List[str]
        """
        return self._team2

    @team2.setter
    def team2(self, team2: List[str]):
        """Sets the team2 of this PvPRequestFullTeams.

        Team used by players to battle each others.  # noqa: E501

        :param team2: The team2 of this PvPRequestFullTeams.
        :type team2: List[str]
        """
        if team2 is not None and len(team2) > 7:
            raise ValueError("Invalid value for `team2`, number of items must be less than or equal to `7`")  # noqa: E501
        if team2 is not None and len(team2) < 7:
            raise ValueError("Invalid value for `team2`, number of items must be greater than or equal to `7`")  # noqa: E501

        self._team2 = team2
