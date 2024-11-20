import unittest

from flask import json

from openapi_server.models.get_inventory_item_request import GetInventoryItemRequest  # noqa: E501
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest  # noqa: E501
from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerInventoryController(BaseTestCase):
    """DbManagerInventoryController integration test stubs"""

    def test_get_inventory_item(self):
        """Test case for get_inventory_item

        
        """
        get_inventory_item_request = openapi_server.GetInventoryItemRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/inventory/get_user_item_info',
            method='POST',
            headers=headers,
            data=json.dumps(get_inventory_item_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_inventory_items(self):
        """Test case for get_user_inventory_items

        
        """
        get_user_involved_auctions_request = openapi_server.GetUserInvolvedAuctionsRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/inventory/get_user_inventory_items',
            method='POST',
            headers=headers,
            data=json.dumps(get_user_involved_auctions_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_item(self):
        """Test case for remove_item

        
        """
        get_inventory_item_request = openapi_server.GetInventoryItemRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/inventory/remove_user_item',
            method='POST',
            headers=headers,
            data=json.dumps(get_inventory_item_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
