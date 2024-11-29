import unittest

from flask import json

from openapi_server.models.exists_profile200_response import ExistsProfile200Response  # noqa: E501
from openapi_server.models.get_currency_from_uuid200_response import GetCurrencyFromUuid200Response  # noqa: E501
from openapi_server.models.get_username_from_uuid200_response import GetUsernameFromUuid200Response  # noqa: E501
from openapi_server.models.get_uuid_from_username200_response import GetUuidFromUsername200Response  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.models.user_full import UserFull  # noqa: E501
from openapi_server.test import BaseTestCase


class TestProfileInternalController(BaseTestCase):
    """ProfileInternalController integration test stubs"""

    def test_add_currency(self):
        """Test case for add_currency

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('amount', 56)]
        headers = { 
        }
        response = self.client.open(
            '/profile/internal/add_currency',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_add_pvp_score(self):
        """Test case for add_pvp_score

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('points_to_add', 56)]
        headers = { 
        }
        response = self.client.open(
            '/profile/internal/add_pvp_score',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_profile_by_uuid(self):
        """Test case for delete_profile_by_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/profile/internal/delete_profile_by_uuid',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_edit_username(self):
        """Test case for edit_username

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('username', 'username_example')]
        headers = { 
        }
        response = self.client.open(
            '/profile/internal/edit_username',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_exists_profile(self):
        """Test case for exists_profile

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/internal/exists',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_currency_from_uuid(self):
        """Test case for get_currency_from_uuid

        
        """
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/internal/get_currency_from_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_profile(self):
        """Test case for get_profile

        
        """
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/internal/get_profile',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_username_from_uuid(self):
        """Test case for get_username_from_uuid

        
        """
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/internal/get_username_from_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_uuid_from_username(self):
        """Test case for get_uuid_from_username

        
        """
        query_string = [('username', 'username_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/internal/get_uuid_from_username',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_insert_profile(self):
        """Test case for insert_profile

        
        """
        query_string = [('user_uuid', 'user_uuid_example'),
                        ('username', 'username_example')]
        headers = { 
        }
        response = self.client.open(
            '/profile/internal/insert_profile',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_profile_list(self):
        """Test case for profile_list

        
        """
        query_string = [('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/internal/list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
