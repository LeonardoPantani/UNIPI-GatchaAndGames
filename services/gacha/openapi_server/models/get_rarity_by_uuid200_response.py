from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server.models.gacha_rarity import GachaRarity
from openapi_server import util

from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501

class GetRarityByUuid200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, rarity=None):  # noqa: E501
        """GetRarityByUuid200Response - a model defined in OpenAPI

        :param rarity: The rarity of this GetRarityByUuid200Response.  # noqa: E501
        :type rarity: GachaRarity
        """
        self.openapi_types = {
            'rarity': GachaRarity
        }

        self.attribute_map = {
            'rarity': 'rarity'
        }

        self._rarity = rarity

    @classmethod
    def from_dict(cls, dikt) -> 'GetRarityByUuid200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_rarity_by_uuid_200_response of this GetRarityByUuid200Response.  # noqa: E501
        :rtype: GetRarityByUuid200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def rarity(self) -> GachaRarity:
        """Gets the rarity of this GetRarityByUuid200Response.


        :return: The rarity of this GetRarityByUuid200Response.
        :rtype: GachaRarity
        """
        return self._rarity

    @rarity.setter
    def rarity(self, rarity: GachaRarity):
        """Sets the rarity of this GetRarityByUuid200Response.


        :param rarity: The rarity of this GetRarityByUuid200Response.
        :type rarity: GachaRarity
        """

        self._rarity = rarity
