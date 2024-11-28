import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.submit_feedback_request import SubmitFeedbackRequest  # noqa: E501
from openapi_server import util


def delete_user_feedbacks(session=None, uuid=None):  # noqa: E501
    """delete_user_feedbacks

    Deletes feedbacks made by the user by UUID, if exist. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def feedback_info(session=None, feedback_id=None):  # noqa: E501
    """feedback_info

    Returns info of a feedback. # noqa: E501

    :param session: 
    :type session: str
    :param feedback_id: 
    :type feedback_id: int

    :rtype: Union[FeedbackWithUsername, Tuple[FeedbackWithUsername, int], Tuple[FeedbackWithUsername, int, Dict[str, str]]
    """
    return 'do some magic!'


def feedback_list(session=None, page_number=None):  # noqa: E501
    """feedback_list

    Returns list of feedbacks based on pagenumber. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[FeedbackPreview], Tuple[List[FeedbackPreview], int], Tuple[List[FeedbackPreview], int, Dict[str, str]]
    """
    return 'do some magic!'


def submit_feedback(submit_feedback_request, session=None, user_uuid=None):  # noqa: E501
    """submit_feedback

    Submits a feedback. # noqa: E501

    :param submit_feedback_request: 
    :type submit_feedback_request: dict | bytes
    :param session: 
    :type session: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        submit_feedback_request = SubmitFeedbackRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
