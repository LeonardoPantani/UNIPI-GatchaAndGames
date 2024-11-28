import unittest

from flask import json

from openapi_server.test import BaseTestCase


class TestFeedbackController(BaseTestCase):
    """FeedbackController integration test stubs"""

    def test_feedback_health_check_get(self):
        """Test case for feedback_health_check_get

        Gives information on service status.
        """
        headers = { 
        }
        response = self.client.open(
            '/feedback/health_check',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_post_feedback(self):
        """Test case for post_feedback

        Sends a feedback.
        """
        query_string = [('string', 'string_example')]
        headers = { 
        }
        response = self.client.open(
            '/feedback/',
            method='POST',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
