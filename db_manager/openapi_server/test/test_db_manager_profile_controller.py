import unittest

from flask import json

from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.edit_user_info_request import EditUserInfoRequest  # noqa: E501
from openapi_server.models.get_user_hash_psw200_response import GetUserHashPsw200Response  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerProfileController(BaseTestCase):
    """DbManagerProfileController integration test stubs"""

    def test_delete_user_profile(self):
        """Test case for delete_user_profile

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/profile/delete',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_edit_user_info(self):
        """Test case for edit_user_info

        
        """
        edit_user_info_request = openapi_server.EditUserInfoRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/profile/edit',
            method='POST',
            headers=headers,
            data=json.dumps(edit_user_info_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_hash_psw(self):
        """Test case for get_user_hash_psw

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/profile/get_user_hashed_psw',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_info(self):
        """Test case for get_user_info

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/profile/get_user_info',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
