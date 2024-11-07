import unittest

from flask import json

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server.models.inventory_item_id import InventoryItemId  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAuctionsController(BaseTestCase):
    """AuctionsController integration test stubs"""

    def test_bid_on_auction(self):
        """Test case for bid_on_auction

        Bids on an active auction
        """
        query_string = [('bid', 1)]
        headers = { 
        }
        response = self.client.open(
            '/auctions/bid/{auction_uuid}'.format(auction_uuid='auction_uuid_example'),
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_create_auction(self):
        """Test case for create_auction

        Creates an auction.
        """
        query_string = [('starting_price', 10),
                        ('gacha_item', openapi_server.InventoryItemId())]
        headers = { 
        }
        response = self.client.open(
            '/auctions/create',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_auction_status(self):
        """Test case for get_auction_status

        Retrieve info on specific auction.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auctions/status/{auction_uuid}'.format(auction_uuid='auction_uuid_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_auctions_history(self):
        """Test case for get_auctions_history

        Retrieve history of my auctions.
        """
        query_string = [('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auctions/history',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_auctions_list(self):
        """Test case for get_auctions_list

        Retrieve the list of auctions.
        """
        query_string = [('status', active),
                        ('rarity', openapi_server.GachaRarity()),
                        ('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/auctions/list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
