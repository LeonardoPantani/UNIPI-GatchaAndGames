import unittest

from flask import json

from openapi_server.models.get_hashed_password200_response import GetHashedPassword200Response  # noqa: E501
from openapi_server.models.get_role_by_uuid200_response import GetRoleByUuid200Response  # noqa: E501
from openapi_server.models.get_user200_response import GetUser200Response  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.models.userinfo_request import UserinfoRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAuthInternalController(BaseTestCase):
    """AuthInternalController integration test stubs"""

    def test_delete_user_by_uuid(self):
        """Test case for delete_user_by_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/auth/internal/delete_user_by_uuid',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_edit_email(self):
        """Test case for edit_email

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('email', 'email_example')]
        headers = { 
        }
        response = self.client.open(
            '/auth/internal/edit_email',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_hashed_password(self):
        """Test case for get_hashed_password

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auth/internal/get_hashed_password',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_role_by_uuid(self):
        """Test case for get_role_by_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auth/internal/get_role_by_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user(self):
        """Test case for get_user

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auth/internal/get_user',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_introspect(self):
        """Test case for introspect

        Validates a Token.
        """
        userinfo_request = openapi_server.UserinfoRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/internal/introspect/',
            method='POST',
            headers=headers,
            data=json.dumps(userinfo_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_userinfo(self):
        """Test case for userinfo

        Returns User Info.
        """
        userinfo_request = openapi_server.UserinfoRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/internal/userinfo/',
            method='POST',
            headers=headers,
            data=json.dumps(userinfo_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
