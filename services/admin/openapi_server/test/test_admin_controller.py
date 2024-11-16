import unittest

from flask import json

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.feedback import Feedback  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAdminController(BaseTestCase):
    """AdminController integration test stubs"""

    def test_ban_profile(self):
        """Test case for ban_profile

        Deletes a profile.
        """
        headers = { 
        }
        response = self.client.open(
            '/admin/profile/{user_uuid}/ban'.format(user_uuid='user_uuid_example'),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_gacha(self):
        """Test case for create_gacha

        Creates a gacha.
        """
        gacha = {"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/admin/gacha/create',
            method='POST',
            headers=headers,
            data=json.dumps(gacha),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_pool(self):
        """Test case for create_pool

        Creates a pool.
        """
        pool = {"name":"Starter Pool","id":"pool_starter","probabilities":{"legendaryProbability":5.962134,"epicProbability":1.4658129,"commonProbability":0.8008282,"rareProbability":6.0274563},"items":[null,null]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/admin/pool/create',
            method='POST',
            headers=headers,
            data=json.dumps(pool),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_gacha(self):
        """Test case for delete_gacha

        Deletes a gacha.
        """
        headers = { 
        }
        response = self.client.open(
            '/admin/gacha/{gacha_uuid}/delete'.format(gacha_uuid='gacha_uuid_example'),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_pool(self):
        """Test case for delete_pool

        Deletes a pool.
        """
        headers = { 
        }
        response = self.client.open(
            '/admin/pool/{pool_id}/delete'.format(pool_id='pool_id_example'),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_edit_user_profile(self):
        """Test case for edit_user_profile

        Edits properties of a profile.
        """
        query_string = [('email', 'email_example'),
                        ('username', 'username_example')]
        headers = { 
        }
        response = self.client.open(
            '/admin/profile/{user_uuid}/edit'.format(user_uuid='user_uuid_example'),
            method='PUT',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_all_feedbacks(self):
        """Test case for get_all_feedbacks

        Returns all feedbacks.
        """
        query_string = [('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/admin/feedback/list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_all_profiles(self):
        """Test case for get_all_profiles

        Returns all profiles.
        """
        query_string = [('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/admin/profile/list/',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_feedback_info(self):
        """Test case for get_feedback_info

        Shows infos on a feedback.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/admin/feedback/{feedback_uuid}'.format(feedback_uuid='feedback_uuid_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_system_logs(self):
        """Test case for get_system_logs

        Returns the system logs.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/admin/logs/',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_history(self):
        """Test case for get_user_history

        Returns history of a user.
        """
        query_string = [('type', 'type_example'),
                        ('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/admin/profile/{user_uuid}/history'.format(user_uuid='user_uuid_example'),
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_health_check(self):
        """Test case for health_check

        Gives information on service status.
        """
        headers = { 
        }
        response = self.client.open(
            '/admin/health_check',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_auction(self):
        """Test case for update_auction

        Updates an auction.
        """
        auction = {"auction_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","inventory_item_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","starting_price":0.8008282,"end_time":"2000-01-23T04:56:07.000+00:00","inventory_item_owner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","current_bid":6.0274563,"status":"active","current_bidder":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/admin/auctions/{auction_uuid}/update'.format(auction_uuid='auction_uuid_example'),
            method='PUT',
            headers=headers,
            data=json.dumps(auction),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_gacha(self):
        """Test case for update_gacha

        Updates a gacha.
        """
        gacha = {"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/admin/gacha/{gacha_uuid}/update'.format(gacha_uuid='gacha_uuid_example'),
            method='PUT',
            headers=headers,
            data=json.dumps(gacha),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_pool(self):
        """Test case for update_pool

        Updates a pool.
        """
        pool = {"name":"Starter Pool","id":"pool_starter","probabilities":{"legendaryProbability":5.962134,"epicProbability":1.4658129,"commonProbability":0.8008282,"rareProbability":6.0274563},"items":[null,null]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/admin/pool/{pool_id}/update'.format(pool_id='pool_id_example'),
            method='PUT',
            headers=headers,
            data=json.dumps(pool),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
