from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetStandUuidByItemUuid200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, stand_uuid=None):  # noqa: E501
        """GetStandUuidByItemUuid200Response - a model defined in OpenAPI

        :param stand_uuid: The stand_uuid of this GetStandUuidByItemUuid200Response.  # noqa: E501
        :type stand_uuid: str
        """
        self.openapi_types = {
            'stand_uuid': str
        }

        self.attribute_map = {
            'stand_uuid': 'stand_uuid'
        }

        self._stand_uuid = stand_uuid

    @classmethod
    def from_dict(cls, dikt) -> 'GetStandUuidByItemUuid200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_stand_uuid_by_item_uuid_200_response of this GetStandUuidByItemUuid200Response.  # noqa: E501
        :rtype: GetStandUuidByItemUuid200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def stand_uuid(self) -> str:
        """Gets the stand_uuid of this GetStandUuidByItemUuid200Response.

        UUID of the gacha  # noqa: E501

        :return: The stand_uuid of this GetStandUuidByItemUuid200Response.
        :rtype: str
        """
        return self._stand_uuid

    @stand_uuid.setter
    def stand_uuid(self, stand_uuid: str):
        """Sets the stand_uuid of this GetStandUuidByItemUuid200Response.

        UUID of the gacha  # noqa: E501

        :param stand_uuid: The stand_uuid of this GetStandUuidByItemUuid200Response.
        :type stand_uuid: str
        """

        self._stand_uuid = stand_uuid