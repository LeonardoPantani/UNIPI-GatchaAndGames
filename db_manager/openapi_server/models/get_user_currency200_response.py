from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetUserCurrency200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, currency=None):  # noqa: E501
        """GetUserCurrency200Response - a model defined in OpenAPI

        :param currency: The currency of this GetUserCurrency200Response.  # noqa: E501
        :type currency: int
        """
        self.openapi_types = {
            'currency': int
        }

        self.attribute_map = {
            'currency': 'currency'
        }

        self._currency = currency

    @classmethod
    def from_dict(cls, dikt) -> 'GetUserCurrency200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_user_currency_200_response of this GetUserCurrency200Response.  # noqa: E501
        :rtype: GetUserCurrency200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def currency(self) -> int:
        """Gets the currency of this GetUserCurrency200Response.

        Currency of the user.  # noqa: E501

        :return: The currency of this GetUserCurrency200Response.
        :rtype: int
        """
        return self._currency

    @currency.setter
    def currency(self, currency: int):
        """Sets the currency of this GetUserCurrency200Response.

        Currency of the user.  # noqa: E501

        :param currency: The currency of this GetUserCurrency200Response.
        :type currency: int
        """
        if currency is not None and currency < 0:  # noqa: E501
            raise ValueError("Invalid value for `currency`, must be a value greater than or equal to `0`")  # noqa: E501

        self._currency = currency
