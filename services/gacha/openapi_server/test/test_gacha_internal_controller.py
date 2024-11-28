import unittest

from flask import json

from openapi_server.models.exists_gacha200_response import ExistsGacha200Response  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_rarity_by_uuid200_response import GetRarityByUuid200Response  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.test import BaseTestCase


class TestGachaInternalController(BaseTestCase):
    """GachaInternalController integration test stubs"""

    def test_create_gacha(self):
        """Test case for create_gacha

        
        """
        gacha = {"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/gacha/create',
            method='POST',
            headers=headers,
            data=json.dumps(gacha),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_pool(self):
        """Test case for create_pool

        
        """
        pool = {"probability_rare":6.0274563,"price":15,"codename":"pool_starter","probability_epic":1.4658129,"probability_common":0.8008282,"probability_legendary":5.962134,"public_name":"Starter Pool","items":[null,null]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/pool/create',
            method='POST',
            headers=headers,
            data=json.dumps(pool),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_gacha(self):
        """Test case for delete_gacha

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/gacha/internal/gacha/delete',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_pool(self):
        """Test case for delete_pool

        
        """
        query_string = [('codename', 'codename_example')]
        headers = { 
        }
        response = self.client.open(
            '/gacha/internal/pool/delete',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_exists_gacha(self):
        """Test case for exists_gacha

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/gacha/exists',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_exists_pool(self):
        """Test case for exists_pool

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/pool/exists',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_gacha(self):
        """Test case for get_gacha

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/gacha/get',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pool(self):
        """Test case for get_pool

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/pool/get',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_rarity_by_uuid(self):
        """Test case for get_rarity_by_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/get_rarity_by_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_gachas(self):
        """Test case for list_gachas

        
        """
        request_body = ['request_body_example']
        query_string = [('not_owned', True)]
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/gacha/list',
            method='POST',
            headers=headers,
            data=json.dumps(request_body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_pools(self):
        """Test case for list_pools

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/pool/list',
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_gacha(self):
        """Test case for update_gacha

        
        """
        gacha = {"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/gacha/update',
            method='POST',
            headers=headers,
            data=json.dumps(gacha),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_pool(self):
        """Test case for update_pool

        
        """
        pool = {"probability_rare":6.0274563,"price":15,"codename":"pool_starter","probability_epic":1.4658129,"probability_common":0.8008282,"probability_legendary":5.962134,"public_name":"Starter Pool","items":[null,null]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/gacha/internal/pool/update',
            method='POST',
            headers=headers,
            data=json.dumps(pool),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
