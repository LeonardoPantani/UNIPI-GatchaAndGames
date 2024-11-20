from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetFeedbackListRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, page_number=1):  # noqa: E501
        """GetFeedbackListRequest - a model defined in OpenAPI

        :param page_number: The page_number of this GetFeedbackListRequest.  # noqa: E501
        :type page_number: int
        """
        self.openapi_types = {
            'page_number': int
        }

        self.attribute_map = {
            'page_number': 'page_number'
        }

        self._page_number = page_number

    @classmethod
    def from_dict(cls, dikt) -> 'GetFeedbackListRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_feedback_list_request of this GetFeedbackListRequest.  # noqa: E501
        :rtype: GetFeedbackListRequest
        """
        return util.deserialize_model(dikt, cls)

    @property
    def page_number(self) -> int:
        """Gets the page_number of this GetFeedbackListRequest.

        Page number, when needed.  # noqa: E501

        :return: The page_number of this GetFeedbackListRequest.
        :rtype: int
        """
        return self._page_number

    @page_number.setter
    def page_number(self, page_number: int):
        """Sets the page_number of this GetFeedbackListRequest.

        Page number, when needed.  # noqa: E501

        :param page_number: The page_number of this GetFeedbackListRequest.
        :type page_number: int
        """
        if page_number is not None and page_number < 1:  # noqa: E501
            raise ValueError("Invalid value for `page_number`, must be a value greater than or equal to `1`")  # noqa: E501

        self._page_number = page_number