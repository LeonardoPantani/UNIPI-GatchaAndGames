import unittest

from flask import json

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server.models.get_bundle_info200_response import GetBundleInfo200Response  # noqa: E501
from openapi_server.models.get_bundle_info_request import GetBundleInfoRequest  # noqa: E501
from openapi_server.models.purchase_bundle_request import PurchaseBundleRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerCurrencyController(BaseTestCase):
    """DbManagerCurrencyController integration test stubs"""

    def test_get_bundle_info(self):
        """Test case for get_bundle_info

        
        """
        get_bundle_info_request = openapi_server.GetBundleInfoRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/currency/get_bundle_info',
            method='POST',
            headers=headers,
            data=json.dumps(get_bundle_info_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_bundles(self):
        """Test case for list_bundles

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/db_manager/currency/list_bundles',
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_purchase_bundle(self):
        """Test case for purchase_bundle

        
        """
        purchase_bundle_request = openapi_server.PurchaseBundleRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/currency/purchase_bundle',
            method='POST',
            headers=headers,
            data=json.dumps(purchase_bundle_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
