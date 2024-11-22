from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server.models.pv_p_request_full import PvPRequestFull
from openapi_server import util

from openapi_server.models.pv_p_request_full import PvPRequestFull  # noqa: E501

class SetMatchResultsRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, match=None, points=None):  # noqa: E501
        """SetMatchResultsRequest - a model defined in OpenAPI

        :param match: The match of this SetMatchResultsRequest.  # noqa: E501
        :type match: PvPRequestFull
        :param points: The points of this SetMatchResultsRequest.  # noqa: E501
        :type points: int
        """
        self.openapi_types = {
            'match': PvPRequestFull,
            'points': int
        }

        self.attribute_map = {
            'match': 'match',
            'points': 'points'
        }

        self._match = match
        self._points = points

    @classmethod
    def from_dict(cls, dikt) -> 'SetMatchResultsRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The set_match_results_request of this SetMatchResultsRequest.  # noqa: E501
        :rtype: SetMatchResultsRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def match(self) -> PvPRequestFull:
        """Gets the match of this SetMatchResultsRequest.


        :return: The match of this SetMatchResultsRequest.
        :rtype: PvPRequestFull
        """
        return self._match

    @match.setter
    def match(self, match: PvPRequestFull):
        """Sets the match of this SetMatchResultsRequest.


        :param match: The match of this SetMatchResultsRequest.
        :type match: PvPRequestFull
        """

        self._match = match

    @property
    def points(self) -> int:
        """Gets the points of this SetMatchResultsRequest.

        Match adds 1 for each game won by player1 and subtracts 1 for each game won by player2  # noqa: E501

        :return: The points of this SetMatchResultsRequest.
        :rtype: int
        """
        return self._points

    @points.setter
    def points(self, points: int):
        """Sets the points of this SetMatchResultsRequest.

        Match adds 1 for each game won by player1 and subtracts 1 for each game won by player2  # noqa: E501

        :param points: The points of this SetMatchResultsRequest.
        :type points: int
        """

        self._points = points
