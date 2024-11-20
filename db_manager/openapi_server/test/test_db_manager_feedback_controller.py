import unittest

from flask import json

from openapi_server.models.submit_feedback_request import SubmitFeedbackRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestDbManagerFeedbackController(BaseTestCase):
    """DbManagerFeedbackController integration test stubs"""

    def test_submit_feedback(self):
        """Test case for submit_feedback

        
        """
        submit_feedback_request = openapi_server.SubmitFeedbackRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/db_manager/feedback/submit',
            method='POST',
            headers=headers,
            data=json.dumps(submit_feedback_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
