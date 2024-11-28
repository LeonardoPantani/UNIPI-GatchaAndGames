import unittest

from flask import json

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server.models.get_user_history200_response import GetUserHistory200Response  # noqa: E501
from openapi_server.test import BaseTestCase


class TestCurrencyInternalController(BaseTestCase):
    """CurrencyInternalController integration test stubs"""

    def test_delete_user_transactions(self):
        """Test case for delete_user_transactions

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/currency/internal/delete_user_transactions',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_bundle(self):
        """Test case for get_bundle

        
        """
        query_string = [('codename', 'codename_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/currency/internal/get_bundle',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_history(self):
        """Test case for get_user_history

        Returns history of a user.
        """
        query_string = [('uuid', 'uuid_example'),
                        ('history_type', 'history_type_example'),
                        ('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/currency/internal/get_user_history',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_insert_bundle_transaction(self):
        """Test case for insert_bundle_transaction

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('bundle_codename', 'bundle_codename_example'),
                        ('currency_name', 'currency_name_example')]
        headers = { 
        }
        response = self.client.open(
            '/currency/internal/insert_bundle_transaction',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_insert_ingame_transaction(self):
        """Test case for insert_ingame_transaction

        
        """
        query_string = [('uuid', 'uuid_example'),
                        ('current_bid', 56),
                        ('transaction_type', 'transaction_type_example')]
        headers = { 
        }
        response = self.client.open(
            '/currency/internal/insert_ingame_transaction',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_bundles(self):
        """Test case for list_bundles

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/currency/internal/list_bundles',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
