import unittest

from flask import json

from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.submit_feedback_request import SubmitFeedbackRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestFeedbackInternalController(BaseTestCase):
    """FeedbackInternalController integration test stubs"""

    def test_delete_user_feedbacks(self):
        """Test case for delete_user_feedbacks

        
        """
        query_string = [('uuid', 'uuid_example')]
        headers = { 
        }
        response = self.client.open(
            '/feedback/internal/delete_user_feedbacks',
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_feedback_info(self):
        """Test case for feedback_info

        
        """
        query_string = [('feedback_id', 56)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/feedback/internal/info',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_feedback_list(self):
        """Test case for feedback_list

        
        """
        query_string = [('page_number', 1)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/feedback/internal/list',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_submit_feedback(self):
        """Test case for submit_feedback

        
        """
        submit_feedback_request = openapi_server.SubmitFeedbackRequest()
        query_string = [('user_uuid', 'user_uuid_example')]
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/feedback/internal/submit',
            method='POST',
            headers=headers,
            data=json.dumps(submit_feedback_request),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
