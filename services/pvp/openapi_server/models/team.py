from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class Team(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, gachas=None):  # noqa: E501
        """Team - a model defined in OpenAPI

        :param gachas: The gachas of this Team.  # noqa: E501
        :type gachas: List[str]
        """
        self.openapi_types = {
            'gachas': List[str]
        }

        self.attribute_map = {
            'gachas': 'gachas'
        }

        self._gachas = gachas

    @classmethod
    def from_dict(cls, dikt) -> 'Team':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Team of this Team.  # noqa: E501
        :rtype: Team
        """
        return util.deserialize_model(dikt, cls)

    @property
    def gachas(self) -> List[str]:
        """Gets the gachas of this Team.


        :return: The gachas of this Team.
        :rtype: List[str]
        """
        return self._gachas

    @gachas.setter
    def gachas(self, gachas: List[str]):
        """Sets the gachas of this Team.


        :param gachas: The gachas of this Team.
        :type gachas: List[str]
        """
        if gachas is not None and len(gachas) > 7:
            raise ValueError("Invalid value for `gachas`, number of items must be less than or equal to `7`")  # noqa: E501
        if gachas is not None and len(gachas) < 7:
            raise ValueError("Invalid value for `gachas`, number of items must be greater than or equal to `7`")  # noqa: E501

        self._gachas = gachas