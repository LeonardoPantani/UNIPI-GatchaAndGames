from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class ExistsInventory200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, exists=None):  # noqa: E501
        """ExistsInventory200Response - a model defined in OpenAPI

        :param exists: The exists of this ExistsInventory200Response.  # noqa: E501
        :type exists: bool
        """
        self.openapi_types = {
            'exists': bool
        }

        self.attribute_map = {
            'exists': 'exists'
        }

        self._exists = exists

    @classmethod
    def from_dict(cls, dikt) -> 'ExistsInventory200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The exists_inventory_200_response of this ExistsInventory200Response.  # noqa: E501
        :rtype: ExistsInventory200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def exists(self) -> bool:
        """Gets the exists of this ExistsInventory200Response.


        :return: The exists of this ExistsInventory200Response.
        :rtype: bool
        """
        return self._exists

    @exists.setter
    def exists(self, exists: bool):
        """Sets the exists of this ExistsInventory200Response.


        :param exists: The exists of this ExistsInventory200Response.
        :type exists: bool
        """

        self._exists = exists
