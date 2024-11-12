import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server import util


def post_feedback(string, session=None):  # noqa: E501
    """Sends a feedback.

    Creates a feedback to the admins. # noqa: E501

    :param string: 
    :type string: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'
