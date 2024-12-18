from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model import Model
from openapi_server import util


class GetCurrencyFromUuid200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, currency=None):  # noqa: E501
        """GetCurrencyFromUuid200Response - a model defined in OpenAPI

        :param currency: The currency of this GetCurrencyFromUuid200Response.  # noqa: E501
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
    def from_dict(cls, dikt) -> 'GetCurrencyFromUuid200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The get_currency_from_uuid_200_response of this GetCurrencyFromUuid200Response.  # noqa: E501
        :rtype: GetCurrencyFromUuid200Response
        """
        return util.deserialize_model(dikt, cls)

    @property
    def currency(self) -> int:
        """Gets the currency of this GetCurrencyFromUuid200Response.


        :return: The currency of this GetCurrencyFromUuid200Response.
        :rtype: int
        """
        return self._currency

    @currency.setter
    def currency(self, currency: int):
        """Sets the currency of this GetCurrencyFromUuid200Response.


        :param currency: The currency of this GetCurrencyFromUuid200Response.
        :type currency: int
        """

        self._currency = currency
