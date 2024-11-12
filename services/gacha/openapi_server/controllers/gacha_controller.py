import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util


def get_gacha_info(gacha_uuid, session=None):  # noqa: E501
    """Shows infos on a gacha.

    Returns infos on a gacha. # noqa: E501

    :param gacha_uuid: 
    :type gacha_uuid: str
    :type gacha_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[Gacha, Tuple[Gacha, int], Tuple[Gacha, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_gachas(not_owned=None):  # noqa: E501
    """Lists all gachas.

    Returns a list of all gachas. # noqa: E501

    :param not_owned: 
    :type not_owned: bool

    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pool_info():  # noqa: E501
    """Lists available pools.

    Returns a list of available gacha pools. # noqa: E501


    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]
    """
    return 'do some magic!'


def pull_gacha(pool_id, session=None):  # noqa: E501
    """Pull a random gacha from a specific pool.

    Allows a player to pull a random gacha item from a specified pool. Consumes in-game currency. # noqa: E501

    :param pool_id: 
    :type pool_id: str
    :param session: 
    :type session: str

    :rtype: Union[Gacha, Tuple[Gacha, int], Tuple[Gacha, int, Dict[str, str]]
    """
    return 'do some magic!'
