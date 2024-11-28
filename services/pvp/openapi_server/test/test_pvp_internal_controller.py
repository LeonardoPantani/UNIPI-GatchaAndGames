import unittest

from flask import json

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestPvpInternalController(BaseTestCase):
    """PvpInternalController integration test stubs"""

    def test_delete_match(self):
        """Test case for delete_match

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/pvp/internal/delete_match',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pending_list(self):
        """Test case for get_pending_list

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/pvp/internal/get_pending_list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_status(self):
        """Test case for get_status

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/pvp/internal/get_status',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_insert_match(self):
        """Test case for insert_match

        
        """
        pv_p_request = {"teams":{"team1":[null,null,null,null,null]},"match_log":{"rounds":[{"player1":{"stand_name":"Tower of Gray","stand_stat":"A"},"player2":{"stand_name":"Tower of Gray","stand_stat":"A"},"extracted_stat":"power","round_winner":"Player1's Tower of Gray"},{"player1":{"stand_name":"Tower of Gray","stand_stat":"A"},"player2":{"stand_name":"Tower of Gray","stand_stat":"A"},"extracted_stat":"power","round_winner":"Player1's Tower of Gray"}]},"receiver_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","match_timestamp":"2000-01-23T04:56:07.000+00:00","pvp_match_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","winner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","sender_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/pvp/internal/insert_match',
            method='POST',
            headers=headers,
            data=json.dumps(pv_p_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_by_user_uuid(self):
        """Test case for remove_by_user_uuid

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/pvp/internal/remove_by_user_uuid',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_set_results(self):
        """Test case for set_results

        
        """
        pv_p_request = {"teams":{"team1":[null,null,null,null,null]},"match_log":{"rounds":[{"player1":{"stand_name":"Tower of Gray","stand_stat":"A"},"player2":{"stand_name":"Tower of Gray","stand_stat":"A"},"extracted_stat":"power","round_winner":"Player1's Tower of Gray"},{"player1":{"stand_name":"Tower of Gray","stand_stat":"A"},"player2":{"stand_name":"Tower of Gray","stand_stat":"A"},"extracted_stat":"power","round_winner":"Player1's Tower of Gray"}]},"receiver_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","match_timestamp":"2000-01-23T04:56:07.000+00:00","pvp_match_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","winner_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","sender_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/pvp/internal/set_results',
            method='POST',
            headers=headers,
            data=json.dumps(pv_p_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
