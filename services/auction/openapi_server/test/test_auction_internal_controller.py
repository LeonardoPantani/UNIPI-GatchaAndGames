import unittest

from flask import json

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.auction_status import AuctionStatus  # noqa: E501
from openapi_server.models.exists_auctions200_response import ExistsAuctions200Response  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server.models.is_open_by_item_uuid200_response import IsOpenByItemUuid200Response  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAuctionInternalController(BaseTestCase):
    """AuctionInternalController integration test stubs"""

    def test_create_auction(self):
        """Test case for create_auction

        
        """
        auction = {"auction_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","inventory_item_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","starting_price":0.8008282,"end_time":"2000-01-23T04:56:07.000+00:00","inventory_item_owner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","current_bid":6.0274563,"status":"open","current_bidder":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/create',
            method='POST',
            headers=headers,
            data=json.dumps(auction),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_exists_auctions(self):
        """Test case for exists_auctions

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/exists',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_auction(self):
        """Test case for get_auction

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/get_auction',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_auction_list(self):
        """Test case for get_auction_list

        
        """
        query_string = [('status', open),
                        ('rarity', openapi_server.GachaRarity()),
                        ('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_auctions(self):
        """Test case for get_user_auctions

        
        """
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/get_user_auctions',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_is_open_by_item_uuid(self):
        """Test case for is_open_by_item_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/is_open_by_item_uuid',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_refund_bidders(self):
        """Test case for refund_bidders

        
        """
        request_body = ['request_body_example']
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/refund_bidders',
            method='POST',
            headers=headers,
            data=json.dumps(request_body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_by_item_uuid(self):
        """Test case for remove_by_item_uuid

        
        """
        request_body = ['request_body_example']
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/remove_by_item_uuid',
            method='POST',
            headers=headers,
            data=json.dumps(request_body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_reset_current_bidder(self):
        """Test case for reset_current_bidder

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/auction/internal/reset_current_bidder',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_set_bid(self):
        """Test case for set_bid

        
        """
        query_string = [('auction_uuid', 'auction_uuid_example'),
                        ('user_uuid', 'user_uuid_example'),
                        ('new_bid', 56)]
        headers = { 
        }
        response = self.client.open(
            '/auction/internal/set_bid',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_auction(self):
        """Test case for update_auction

        
        """
        auction = {"auction_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","inventory_item_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","starting_price":0.8008282,"end_time":"2000-01-23T04:56:07.000+00:00","inventory_item_owner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","current_bid":6.0274563,"status":"open","current_bidder":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/auction/internal/update',
            method='POST',
            headers=headers,
            data=json.dumps(auction),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
