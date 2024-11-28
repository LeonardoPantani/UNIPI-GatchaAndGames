import unittest

from flask import json

from openapi_server.models.check_owner_of_team_request import CheckOwnerOfTeamRequest  # noqa: E501
from openapi_server.models.exists_inventory200_response import ExistsInventory200Response  # noqa: E501
from openapi_server.models.get_stand_uuid_by_item_uuid200_response import GetStandUuidByItemUuid200Response  # noqa: E501
from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server.test import BaseTestCase


class TestInventoryInternalController(BaseTestCase):
    """InventoryInternalController integration test stubs"""

    def test_check_owner_of_team(self):
        """Test case for check_owner_of_team

        
        """
        check_owner_of_team_request = openapi_server.CheckOwnerOfTeamRequest()
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/check_owner_of_team',
            method='POST',
            headers=headers,
            data=json.dumps(check_owner_of_team_request),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_by_stand_uuid(self):
        """Test case for delete_by_stand_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/inventory/internal/delete_by_stand_uuid',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_user_inventory(self):
        """Test case for delete_user_inventory

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/inventory/internal/delete_user_inventory',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_exists_inventory(self):
        """Test case for exists_inventory

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/exists',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_gachas_types_of_user(self):
        """Test case for get_gachas_types_of_user

        
        """
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/get_gachas_types_of_user',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_inventory_by_owner_uuid(self):
        """Test case for get_inventory_by_owner_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/get_items_by_owner_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_inventory_items_by_owner_uuid(self):
        """Test case for get_inventory_items_by_owner_uuid

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/list_inventory_items',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_item_by_uuid(self):
        """Test case for get_item_by_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/get_by_item_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_items_by_stand_uuid(self):
        """Test case for get_items_by_stand_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/get_items_by_stand_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_stand_uuid_by_item_uuid(self):
        """Test case for get_stand_uuid_by_item_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/get_stand_uuid_by_item_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_insert_item(self):
        """Test case for insert_item

        
        """
        inventory_item = {"item_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","obtained_date":"2000-01-23T04:56:07.000+00:00","price_paid":6.0274563,"owner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","owners_no":0}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/inventory/internal/insert_item',
            method='POST',
            headers=headers,
            data=json.dumps(inventory_item),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_item(self):
        """Test case for remove_item

        
        """
        query_string = [('item_uuid', 'item_uuid_example'),
                        ('owner_uuid', 'owner_uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/inventory/internal/remove',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_item_ownership(self):
        """Test case for update_item_ownership

        
        """
        query_string = [('new_owner_uuid', 'new_owner_uuid_example'),
                        ('item_uuid', 'item_uuid_example'),
                        ('price_paid', 56)]
        headers = { 
        }
        response = self.client.open(
            '/inventory/internal/update_item_owner',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
