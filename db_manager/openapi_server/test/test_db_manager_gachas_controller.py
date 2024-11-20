import unittest

from flask import json

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_gacha_info_request import GetGachaInfoRequest  # noqa: E501
from openapi_server.models.get_gacha_list_request import GetGachaListRequest  # noqa: E501
from openapi_server.models.give_item_request import GiveItemRequest  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerGachasController(BaseTestCase):
    """DbManagerGachasController integration test stubs"""

    def test_get_gacha_info(self):
        """Test case for get_gacha_info

        
        """
        get_gacha_info_request = openapi_server.GetGachaInfoRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/gachas/get_gacha_info',
            method='POST',
            headers=headers,
            data=json.dumps(get_gacha_info_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_gacha_list(self):
        """Test case for get_gacha_list

        
        """
        get_gacha_list_request = openapi_server.GetGachaListRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/gachas/get_gacha_list',
            method='POST',
            headers=headers,
            data=json.dumps(get_gacha_list_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pool_info(self):
        """Test case for get_pool_info

        
        """
        body = 'body_example'
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/gachas/get_pool_info',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pools_list(self):
        """Test case for get_pools_list

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/db_manager/gachas/get_pools',
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_give_item(self):
        """Test case for give_item

        
        """
        give_item_request = openapi_server.GiveItemRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/gachas/give_item',
            method='POST',
            headers=headers,
            data=json.dumps(give_item_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
