from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class MatchPairingPlayer2(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, stand_stat=None):  # noqa: E501
        """MatchPairingPlayer2 - a model defined in OpenAPI

        :param stand_stat: The stand_stat of this MatchPairingPlayer2.  # noqa: E501
        :type stand_stat: int
        """
        self.openapi_types = {
            'stand_stat': int
        }

        self.attribute_map = {
            'stand_stat': 'stand_stat'
        }

        self._stand_stat = stand_stat

    @classmethod
    def from_dict(cls, dikt) -> 'MatchPairingPlayer2':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The MatchPairing_player2 of this MatchPairingPlayer2.  # noqa: E501
        :rtype: MatchPairingPlayer2
        """
        return util.deserialize_model(dikt, cls)

    @property
    def stand_stat(self) -> int:
        """Gets the stand_stat of this MatchPairingPlayer2.

        Value of extracted_stat  # noqa: E501

        :return: The stand_stat of this MatchPairingPlayer2.
        :rtype: int
        """
        return self._stand_stat

    @stand_stat.setter
    def stand_stat(self, stand_stat: int):
        """Sets the stand_stat of this MatchPairingPlayer2.

        Value of extracted_stat  # noqa: E501

        :param stand_stat: The stand_stat of this MatchPairingPlayer2.
        :type stand_stat: int
        """
        if stand_stat is not None and stand_stat > 5:  # noqa: E501
            raise ValueError("Invalid value for `stand_stat`, must be a value less than or equal to `5`")  # noqa: E501
        if stand_stat is not None and stand_stat < 1:  # noqa: E501
            raise ValueError("Invalid value for `stand_stat`, must be a value greater than or equal to `1`")  # noqa: E501

        self._stand_stat = stand_stat
