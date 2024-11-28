import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.exists_gacha200_response import ExistsGacha200Response  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_rarity_by_uuid200_response import GetRarityByUuid200Response  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util


def create_gacha(gacha, session=None):  # noqa: E501
    """create_gacha

    Creates gacha requested. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_pool(pool, session=None):  # noqa: E501
    """create_pool

    Creates pool requested. # noqa: E501

    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_gacha(session=None, uuid=None):  # noqa: E501
    """delete_gacha

    Deletes requested gacha, also from pool item list. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_pool(session=None, codename=None):  # noqa: E501
    """delete_pool

    Deletes requested pool. # noqa: E501

    :param session: 
    :type session: str
    :param codename: 
    :type codename: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def exists_gacha(session=None, uuid=None):  # noqa: E501
    """exists_gacha

    Returns true if an gacha exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[ExistsGacha200Response, Tuple[ExistsGacha200Response, int], Tuple[ExistsGacha200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def exists_pool(session=None, uuid=None):  # noqa: E501
    """exists_pool

    Returns true if a pool exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str

    :rtype: Union[ExistsGacha200Response, Tuple[ExistsGacha200Response, int], Tuple[ExistsGacha200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_gacha(session=None, uuid=None):  # noqa: E501
    """get_gacha

    Returns the gacha object by gacha uuid. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[Gacha, Tuple[Gacha, int], Tuple[Gacha, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pool(session=None, uuid=None):  # noqa: E501
    """get_pool

    Returns true if a pool exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str

    :rtype: Union[Pool, Tuple[Pool, int], Tuple[Pool, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_rarity_by_uuid(session=None, uuid=None):  # noqa: E501
    """get_rarity_by_uuid

    Returns the rarity of a certain gacha identified by its uuid. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[GetRarityByUuid200Response, Tuple[GetRarityByUuid200Response, int], Tuple[GetRarityByUuid200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def list_gachas(request_body, session=None, not_owned=None):  # noqa: E501
    """list_gachas

    Returns list of gachas (not) owned by the user. # noqa: E501

    :param request_body: 
    :type request_body: List[str]
    :param session: 
    :type session: str
    :param not_owned: 
    :type not_owned: bool

    :rtype: Union[List[Gacha], Tuple[List[Gacha], int], Tuple[List[Gacha], int, Dict[str, str]]
    """
    return 'do some magic!'


def list_pools(session=None):  # noqa: E501
    """list_pools

    Returns list of pools. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]
    """
    return 'do some magic!'


def update_gacha(session=None, gacha=None):  # noqa: E501
    """update_gacha

    Updates a gacha. # noqa: E501

    :param session: 
    :type session: str
    :param gacha: 
    :type gacha: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_pool(pool, session=None):  # noqa: E501
    """update_pool

    Updates a pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
