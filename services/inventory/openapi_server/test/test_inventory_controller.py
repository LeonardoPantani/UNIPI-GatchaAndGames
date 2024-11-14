import unittest

from flask import json

from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server.test import BaseTestCase


class TestInventoryController(BaseTestCase):
    """InventoryController integration test stubs"""

    def test_health_check(self):
        """Test case for health_check

        Gives information on service status.
        """
        response = self.client.open(
            '/inventory/health_check',
            method='GET',
            headers=headers,
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_inventory(self):
        """Test case for get_inventory

        Retrieve player's inventory
        """
        query_string = [('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_inventory_item_info(self):
        """Test case for get_inventory_item_info

        Shows infos on my inventory item.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/{inventory_item_id}'.format(inventory_item_id='inventory_item_id_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_inventory_item(self):
        """Test case for remove_inventory_item

        Removes an item from player's inventory
        """
        query_string = [('inventory_item_owner_id', 'inventory_item_owner_id_example'),
                        ('inventory_item_id', 'inventory_item_id_example')]
        headers = { 
        }
        response = self.client.open(
            '/inventory',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
