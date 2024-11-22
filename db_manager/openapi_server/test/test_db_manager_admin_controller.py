import unittest

from flask import json

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.edit_user_profile_request import EditUserProfileRequest  # noqa: E501
from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_feedback_info_request import GetFeedbackInfoRequest  # noqa: E501
from openapi_server.models.get_feedback_list_request import GetFeedbackListRequest  # noqa: E501
from openapi_server.models.get_user_history_request import GetUserHistoryRequest  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerAdminController(BaseTestCase):
    """DbManagerAdminController integration test stubs"""

    def test_ban_user_profile(self):
        """Test case for ban_user_profile

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/ban_user_profile',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_gacha_pool(self):
        """Test case for create_gacha_pool

        
        """
        pool = {"price":15,"name":"Starter Pool","id":"pool_starter","probabilities":{"legendaryProbability":5.962134,"epicProbability":1.4658129,"commonProbability":0.8008282,"rareProbability":6.0274563},"items":[null,null]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/create_pool',
            method='POST',
            headers=headers,
            data=json.dumps(pool),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_gacha_type(self):
        """Test case for create_gacha_type

        
        """
        gacha = {"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/create_gacha',
            method='POST',
            headers=headers,
            data=json.dumps(gacha),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_gacha_pool(self):
        """Test case for delete_gacha_pool

        
        """
        body = 'body_example'
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/delete_pool',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_gacha_type(self):
        """Test case for delete_gacha_type

        
        """
        body = 'body_example'
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/delete_gacha',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_edit_user_profile(self):
        """Test case for edit_user_profile

        
        """
        edit_user_profile_request = openapi_server.EditUserProfileRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/edit_user_profile',
            method='POST',
            headers=headers,
            data=json.dumps(edit_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_feedback_info(self):
        """Test case for get_feedback_info

        
        """
        get_feedback_info_request = openapi_server.GetFeedbackInfoRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/get_feedback_info',
            method='POST',
            headers=headers,
            data=json.dumps(get_feedback_info_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_feedback_list(self):
        """Test case for get_feedback_list

        
        """
        get_feedback_list_request = openapi_server.GetFeedbackListRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/get_all_feedbacks',
            method='POST',
            headers=headers,
            data=json.dumps(get_feedback_list_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_profile_list(self):
        """Test case for get_profile_list

        
        """
        get_feedback_list_request = openapi_server.GetFeedbackListRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/get_all_profiles',
            method='POST',
            headers=headers,
            data=json.dumps(get_feedback_list_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_history(self):
        """Test case for get_user_history

        
        """
        get_user_history_request = openapi_server.GetUserHistoryRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/get_user_history',
            method='POST',
            headers=headers,
            data=json.dumps(get_user_history_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_auction(self):
        """Test case for update_auction

        
        """
        auction = {"auction_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","inventory_item_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","starting_price":0,"end_time":"2000-01-23T04:56:07.000+00:00","inventory_item_owner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","current_bid":6,"status":"open","current_bidder":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/update_auction',
            method='POST',
            headers=headers,
            data=json.dumps(auction),
            content_type='application/json')
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
            '/db_manager/admin/update_gacha',
            method='POST',
            headers=headers,
            data=json.dumps(gacha),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_pool(self):
        """Test case for update_pool

        
        """
        pool = {"price":15,"name":"Starter Pool","id":"pool_starter","probabilities":{"legendaryProbability":5.962134,"epicProbability":1.4658129,"commonProbability":0.8008282,"rareProbability":6.0274563},"items":[null,null]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/admin/update_pool',
            method='POST',
            headers=headers,
            data=json.dumps(pool),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
