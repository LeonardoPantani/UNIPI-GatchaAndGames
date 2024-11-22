import unittest

from flask import json

from openapi_server.models.login_request import LoginRequest  # noqa: E501
from openapi_server.models.register_request import RegisterRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAuthController(BaseTestCase):
    """AuthController integration test stubs"""

    def test_auth_health_check_get(self):
        """Test case for auth_health_check_get

        Gives information on service status.
        """
        headers = { 
        }
        response = self.client.open(
            '/auth/health_check',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_login(self):
        """Test case for login

        Log in into an account.
        """
        login_request = openapi_server.LoginRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/login',
            method='POST',
            headers=headers,
            data=json.dumps(login_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_logout(self):
        """Test case for logout

        Logs out from an account.
        """
        headers = { 
        }
        response = self.client.open(
            '/auth/logout',
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_register(self):
        """Test case for register

        Registers a new account.
        """
        register_request = openapi_server.RegisterRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auth/register',
            method='POST',
            headers=headers,
            data=json.dumps(register_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
