import unittest

from flask import json

from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.get_gacha_stat200_response import GetGachaStat200Response  # noqa: E501
from openapi_server.models.get_gacha_stat_request import GetGachaStatRequest  # noqa: E501
from openapi_server.models.get_pvp_status_request import GetPvpStatusRequest  # noqa: E501
from openapi_server.models.match_requests_inner import MatchRequestsInner  # noqa: E501
from openapi_server.models.pv_p_request_full import PvPRequestFull  # noqa: E501
from openapi_server.models.reject_pvp_prequest_request import RejectPvpPrequestRequest  # noqa: E501
from openapi_server.models.set_match_results_request import SetMatchResultsRequest  # noqa: E501
from openapi_server.models.verify_gacha_item_ownership_request import VerifyGachaItemOwnershipRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerPvpController(BaseTestCase):
    """DbManagerPvpController integration test stubs"""

    def test_check_pending_pvp_requests(self):
        """Test case for check_pending_pvp_requests

        
        """
        ban_user_profile_request = openapi_server.BanUserProfileRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/check_pending_pvp_requests',
            method='POST',
            headers=headers,
            data=json.dumps(ban_user_profile_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_finalize_pvp_request_sending(self):
        """Test case for finalize_pvp_request_sending

        
        """
        pv_p_request_full = {"winner":True,"teams":{"team1":[null,null,null,null,null],"team2":[null,null,null,null,null]},"match_log":{"pairings":[{"player1":{"stand_stat":4},"player2":{"stand_stat":3},"extracted_stat":"A","pair":"player1 StarPlatinum vs player2 GoldenExperience"},{"player1":{"stand_stat":4},"player2":{"stand_stat":3},"extracted_stat":"A","pair":"player1 StarPlatinum vs player2 GoldenExperience"},{"player1":{"stand_stat":4},"player2":{"stand_stat":3},"extracted_stat":"A","pair":"player1 StarPlatinum vs player2 GoldenExperience"},{"player1":{"stand_stat":4},"player2":{"stand_stat":3},"extracted_stat":"A","pair":"player1 StarPlatinum vs player2 GoldenExperience"},{"player1":{"stand_stat":4},"player2":{"stand_stat":3},"extracted_stat":"A","pair":"player1 StarPlatinum vs player2 GoldenExperience"}]},"receiver_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","pvp_match_uuid":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","sender_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/finalize_pvp_request_sending',
            method='POST',
            headers=headers,
            data=json.dumps(pv_p_request_full),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_gacha_stat(self):
        """Test case for get_gacha_stat

        
        """
        get_gacha_stat_request = openapi_server.GetGachaStatRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/get_gacha_stat',
            method='POST',
            headers=headers,
            data=json.dumps(get_gacha_stat_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pvp_status(self):
        """Test case for get_pvp_status

        
        """
        get_pvp_status_request = openapi_server.GetPvpStatusRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/get_pvp_status',
            method='POST',
            headers=headers,
            data=json.dumps(get_pvp_status_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_reject_pvp_prequest(self):
        """Test case for reject_pvp_prequest

        
        """
        reject_pvp_prequest_request = openapi_server.RejectPvpPrequestRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/reject_pvp_request',
            method='POST',
            headers=headers,
            data=json.dumps(reject_pvp_prequest_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_set_match_results(self):
        """Test case for set_match_results

        
        """
        set_match_results_request = openapi_server.SetMatchResultsRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/set_match_results',
            method='POST',
            headers=headers,
            data=json.dumps(set_match_results_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_verify_gacha_item_ownership(self):
        """Test case for verify_gacha_item_ownership

        
        """
        verify_gacha_item_ownership_request = openapi_server.VerifyGachaItemOwnershipRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/pvp/verify_gacha_item_ownership',
            method='POST',
            headers=headers,
            data=json.dumps(verify_gacha_item_ownership_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
