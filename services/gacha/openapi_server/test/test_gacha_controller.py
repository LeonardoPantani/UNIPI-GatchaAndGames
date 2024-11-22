import unittest

from flask import json

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.test import BaseTestCase


class TestGachaController(BaseTestCase):
    """GachaController integration test stubs"""

    def test_health_check(self):
        """Test case for health_check

        Gives information on service status.
        """
        response = self.client.open(
            '/gacha/health_check',
            method='GET',
            headers=headers,
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_gacha_info(self):
        """Test case for get_gacha_info

        Shows infos on a gacha.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/{gacha_uuid}'.format(gacha_uuid='gacha_uuid_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_gachas(self):
        """Test case for get_gachas

        Lists all gachas.
        """
        query_string = [('not_owned', False)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pool_info(self):
        """Test case for get_pool_info

        Lists available pools.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/pools',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_pull_gacha(self):
        """Test case for pull_gacha

        Pull a random gacha from a specific pool.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/gacha/pull/{pool_id}'.format(pool_id='pool_id_example'),
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
