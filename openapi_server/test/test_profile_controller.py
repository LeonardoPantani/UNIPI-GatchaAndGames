import unittest

from flask import json

from openapi_server.models.delete_profile_request import DeleteProfileRequest  # noqa: E501
from openapi_server.models.edit_profile_request import EditProfileRequest  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestProfileController(BaseTestCase):
    """ProfileController integration test stubs"""

    def test_delete_profile(self):
        """Test case for delete_profile

        Deletes this account.
        """
        delete_profile_request = openapi_server.DeleteProfileRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/profile/delete',
            method='POST',
            headers=headers,
            data=json.dumps(delete_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_edit_profile(self):
        """Test case for edit_profile

        Edits properties of the profile.
        """
        edit_profile_request = openapi_server.EditProfileRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/profile/edit',
            method='PUT',
            headers=headers,
            data=json.dumps(edit_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_info(self):
        """Test case for get_user_info

        Returns infos about a UUID.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/profile/{uuid}/info'.format(uuid='uuid_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
