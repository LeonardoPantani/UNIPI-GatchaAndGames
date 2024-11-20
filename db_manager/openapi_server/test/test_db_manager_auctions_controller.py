import unittest

from flask import json

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.complete_auction_sale_request import CompleteAuctionSaleRequest  # noqa: E501
from openapi_server.models.get_auction_status200_response import GetAuctionStatus200Response  # noqa: E501
from openapi_server.models.get_auction_status_request import GetAuctionStatusRequest  # noqa: E501
from openapi_server.models.get_currency200_response import GetCurrency200Response  # noqa: E501
from openapi_server.models.get_item_with_owner200_response import GetItemWithOwner200Response  # noqa: E501
from openapi_server.models.get_item_with_owner_request import GetItemWithOwnerRequest  # noqa: E501
from openapi_server.models.get_user_currency200_response import GetUserCurrency200Response  # noqa: E501
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest  # noqa: E501
from openapi_server.models.list_auctions_request import ListAuctionsRequest  # noqa: E501
from openapi_server.models.place_bid_request import PlaceBidRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerAuctionsController(BaseTestCase):
    """DbManagerAuctionsController integration test stubs"""

    def test_complete_auction_sale(self):
        """Test case for complete_auction_sale

        
        """
        complete_auction_sale_request = openapi_server.CompleteAuctionSaleRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/complete_sale',
            method='POST',
            headers=headers,
            data=json.dumps(complete_auction_sale_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_auction(self):
        """Test case for create_auction

        
        """
        get_auction_status200_response = openapi_server.GetAuctionStatus200Response()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/create',
            method='POST',
            headers=headers,
            data=json.dumps(get_auction_status200_response),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_auction_status(self):
        """Test case for get_auction_status

        
        """
        get_auction_status_request = openapi_server.GetAuctionStatusRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/get_auction_status',
            method='POST',
            headers=headers,
            data=json.dumps(get_auction_status_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_currency(self):
        """Test case for get_currency

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/gachas/get_currency',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_item_with_owner(self):
        """Test case for get_item_with_owner

        
        """
        get_item_with_owner_request = openapi_server.GetItemWithOwnerRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/get_item_with_owner',
            method='POST',
            headers=headers,
            data=json.dumps(get_item_with_owner_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_currency(self):
        """Test case for get_user_currency

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/get_currency',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_involved_auctions(self):
        """Test case for get_user_involved_auctions

        
        """
        get_user_involved_auctions_request = openapi_server.GetUserInvolvedAuctionsRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/get_user_involved_auctions',
            method='POST',
            headers=headers,
            data=json.dumps(get_user_involved_auctions_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_auctions(self):
        """Test case for list_auctions

        
        """
        list_auctions_request = openapi_server.ListAuctionsRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/list',
            method='POST',
            headers=headers,
            data=json.dumps(list_auctions_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_place_bid(self):
        """Test case for place_bid

        
        """
        place_bid_request = openapi_server.PlaceBidRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/auctions/place_bid',
            method='POST',
            headers=headers,
            data=json.dumps(place_bid_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
