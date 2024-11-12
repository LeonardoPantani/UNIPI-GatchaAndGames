import unittest

from flask import json

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server.test import BaseTestCase


class TestCurrencyController(BaseTestCase):
    """CurrencyController integration test stubs"""

    def test_buy_currency(self):
        """Test case for buy_currency

        Buy in-game credits
        """
        headers = { 
        }
        response = self.client.open(
            '/currency/buy/{bundle_id}'.format(bundle_id='bundle_id_example'),
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_bundles(self):
        """Test case for get_bundles

        Lists available bundles to buy currency.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/currency/bundles',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
