from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server.models.inventory_item import InventoryItem
from openapi_server import util

from openapi_server.models.inventory_item import InventoryItem  # noqa: E501

class GetItemWithOwner200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, item=None):  # noqa: E501
        """GetItemWithOwner200Response - a model defined in OpenAPI

        :param item: The item of this GetItemWithOwner200Response.  # noqa: E501
        :type item: InventoryItem
        """
        self.openapi_types = {
            'item': InventoryItem
        }

        self.attribute_map = {
            'item': 'item'
        }

        self._item = item

    @classmethod
    def from_dict(cls, dikt) -> 'GetItemWithOwner200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_item_with_owner_200_response of this GetItemWithOwner200Response.  # noqa: E501
        :rtype: GetItemWithOwner200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def item(self) -> InventoryItem:
        """Gets the item of this GetItemWithOwner200Response.


        :return: The item of this GetItemWithOwner200Response.
        :rtype: InventoryItem
        """
        return self._item

    @item.setter
    def item(self, item: InventoryItem):
        """Sets the item of this GetItemWithOwner200Response.


        :param item: The item of this GetItemWithOwner200Response.
        :type item: InventoryItem
        """

        self._item = item