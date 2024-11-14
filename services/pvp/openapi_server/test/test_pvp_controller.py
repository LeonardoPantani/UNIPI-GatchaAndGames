import unittest

from flask import json

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server.models.team import Team  # noqa: E501
from openapi_server.test import BaseTestCase


class TestPvpController(BaseTestCase):
    """PvpController integration test stubs"""

    def test_health_check(self):
        """Test case for health_check

        Gives information on service status.
        """
        response = self.client.open(
            '/pvp/health_check',
            method='GET',
            headers=headers,
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_accept_pvp_request(self):
        """Test case for accept_pvp_request

        Accept a pending PvP request.
        """
        team = {"gachas":[{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}]}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/pvp/acceptPvPRequest/{pvp_match_uuid}'.format(pvp_match_uuid='pvp_match_uuid_example'),
            method='POST',
            headers=headers,
            data=json.dumps(team),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_check_pending_pvp_requests(self):
        """Test case for check_pending_pvp_requests

        Returns a list of pending PvP requests.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/pvp/checkPendingPvPRequests',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pvp_status(self):
        """Test case for get_pvp_status

        Returns the results of a PvP match.
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/pvp/status/{pvp_match_uuid}'.format(pvp_match_uuid='pvp_match_uuid_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_reject_pv_prequest(self):
        """Test case for reject_pv_prequest

        Rejects a pending PvP request.
        """
        headers = { 
        }
        response = self.client.open(
            '/pvp/rejectPvPRequest/{pvp_match_uuid}'.format(pvp_match_uuid='pvp_match_uuid_example'),
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_send_pvp_request(self):
        """Test case for send_pvp_request

        Sends a PvP match request.
        """
        team = {"gachas":[{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"},{"gacha_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","name":"Tower of Gray","attributes":{"durability":"A","precision":"A","range":"A","power":"A","potential":"A","speed":"A"},"rarity":"rare"}]}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/pvp/sendPvPRequest/{user_uuid}'.format(user_uuid='user_uuid_example'),
            method='POST',
            headers=headers,
            data=json.dumps(team),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
