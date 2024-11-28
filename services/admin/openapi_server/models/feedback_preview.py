from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class FeedbackPreview(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None, user_uuid=None, timestamp=None):  # noqa: E501
        """FeedbackPreview - a model defined in OpenAPI

        :param id: The id of this FeedbackPreview.  # noqa: E501
        :type id: int
        :param user_uuid: The user_uuid of this FeedbackPreview.  # noqa: E501
        :type user_uuid: str
        :param timestamp: The timestamp of this FeedbackPreview.  # noqa: E501
        :type timestamp: datetime
        """
        self.openapi_types = {
            'id': int,
            'user_uuid': str,
            'timestamp': datetime
        }

        self.attribute_map = {
            'id': 'id',
            'user_uuid': 'user_uuid',
            'timestamp': 'timestamp'
        }

        self._id = id
        self._user_uuid = user_uuid
        self._timestamp = timestamp

    @classmethod
    def from_dict(cls, dikt) -> 'FeedbackPreview':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FeedbackPreview of this FeedbackPreview.  # noqa: E501
        :rtype: FeedbackPreview
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> int:
        """Gets the id of this FeedbackPreview.

        Id of feedback.  # noqa: E501

        :return: The id of this FeedbackPreview.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id: int):
        """Sets the id of this FeedbackPreview.

        Id of feedback.  # noqa: E501

        :param id: The id of this FeedbackPreview.
        :type id: int
        """

        self._id = id

    @property
    def user_uuid(self) -> str:
        """Gets the user_uuid of this FeedbackPreview.

        UUID of user.  # noqa: E501

        :return: The user_uuid of this FeedbackPreview.
        :rtype: str
        """
        return self._user_uuid

    @user_uuid.setter
    def user_uuid(self, user_uuid: str):
        """Sets the user_uuid of this FeedbackPreview.

        UUID of user.  # noqa: E501

        :param user_uuid: The user_uuid of this FeedbackPreview.
        :type user_uuid: str
        """

        self._user_uuid = user_uuid

    @property
    def timestamp(self) -> datetime:
        """Gets the timestamp of this FeedbackPreview.

        Timestamp when user created feedback  # noqa: E501

        :return: The timestamp of this FeedbackPreview.
        :rtype: datetime
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime):
        """Sets the timestamp of this FeedbackPreview.

        Timestamp when user created feedback  # noqa: E501

        :param timestamp: The timestamp of this FeedbackPreview.
        :type timestamp: datetime
        """

        self._timestamp = timestamp