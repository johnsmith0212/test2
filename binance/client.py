import hashlib
import requests
import six
import time
if six.PY2:
    from urllib import urlencode
elif six.PY3:
    from urllib.parse import urlencode

from exceptions import BinanceAPIException


class Client(object):

    API_URL = 'https://www.binance.com/api'
    API_VERSION = 'v1'

    def __init__(self, api_key, api_secret):

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()

    def _init_session(self):

        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def _create_api_uri(self, path):
        return self.API_URL + '/' + self.API_VERSION + '/' + path

    def _generate_signature(self, data):

        query_string = urlencode(data)
        m = hashlib.sha256()
        m.update((self.API_SECRET + '|' + query_string).encode())
        return m.hexdigest()

    def _request(self, method, path, signed, **kwargs):

        uri = self._create_api_uri(path)

        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data
        if signed:
            # generate signature
            kwargs['data']['timestamp'] =int(time.time() * 1000)
            kwargs['data']['signature'] = self._generate_signature(kwargs['data'])

        if data and method == 'get':
            kwargs['params'] = kwargs['data']
            del(kwargs['data'])

        print kwargs

        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    def _handle_response(self, response):
        """Internal helper for handling API responses from the Coinbase server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(response.status_code).startswith('2'):
            raise BinanceAPIException(response)
        return response.json()

    def _get(self, path, signed=False, **kwargs):
        return self._request('get', path, signed, **kwargs)

    def _post(self, path, signed=False, **kwargs):
        return self._request('post', path, signed, **kwargs)

    def _put(self, path, signed=False, **kwargs):
        return self._request('put', path, signed, **kwargs)

    def _delete(self, path, signed=False, **kwargs):
        return self._request('delete', path, signed, **kwargs)

    # General Endpoints

    def ping(self):
        """
        Test connectivity to the Rest API.
        https://www.binance.com/restapipub.html#test-connectivity
        :return:
        """
        return self._get('ping')

    def get_server_time(self):
        """
        Test connectivity to the Rest API and get the current server time.
        https://www.binance.com/restapipub.html#check-server-time
        :return:
        """
        return self._get('time')

    # Market Data Endpoints

    def get_order_book(self, **params):
        """
        Get the Order Book for the market
        https://www.binance.com/restapipub.html#order-book
        :param params:
            symbol - required
            limit - Default 100; max 100
        :return:
        """
        return self._get('depth', data=params)

    def get_aggregate_trades(self, **params):
        """
        Get compressed, aggregate trades. Trades that fill at the time,
        from the same order, with the same price will have the quantity aggregated.
        https://www.binance.com/restapipub.html#compressedaggregate-trades-list
        :param params:
            symbol - required
            fromId - ID to get aggregate trades from INCLUSIVE.
            startTime - Timestamp in ms to get aggregate trades from INCLUSIVE.
            endTime - Timestamp in ms to get aggregate trades until INCLUSIVE.
            limit - Default 500; max 500.
        :return:
        """
        return self._get('aggTrades', data=params)

    def get_klines(self, **params):
        """
        Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.
        https://www.binance.com/restapipub.html#klinecandlesticks
        :param params:
            symbol - required
            interval - enum
            limit - Default 500; max 500.
            startTime -
            endTime -
        :return:
        """
        return self._get('klines', data=params)

    def get_ticker(self, **params):
        """
        24 hour price change statistics.
        https://www.binance.com/restapipub.html#24hr-ticker-price-change-statistics
        :param params:
            symbol - required
        :return:
        """
        return self._get('ticker/24hr', data=params)

    # Account Endpoints

    def create_order(self, **params):
        """
        Send in a new order
        https://www.binance.com/restapipub.html#new-order--signed
        :param params:
            symbol - required
            side - required
            type - required
            timeInForce - required
            quantity - required
            price - required
            newClientOrderId - A unique id for the order. Automatically generated if not sent.
            stopPrice - Used with stop orders
            icebergQty - Used with iceberg orders
        :return:
        """
        return self._post('order', True, data=params)

    def create_test_order(self, **params):
        """
        Test new order creation and signature/recvWindow long. Creates and validates a new order but does not send it into the matching engine.
        https://www.binance.com/restapipub.html#test-new-order-signed
        :param params:
            symbol - required
            side - required enum
            type - required enum
            timeInForce - required enum
            quantity - required
            price - required
            newClientOrderId - A unique id for the order. Automatically generated if not sent.
            stopPrice - Used with stop orders
            icebergQty - Used with iceberg orders
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._post('order/test', True, data=params)

    def get_order(self, **params):
        """
        Check an order's status.
        Either orderId or origClientOrderId must be sent.
        https://www.binance.com/restapipub.html#query-order-signed
        :param params:
            symbol - required
            orderId - The unique order id
            origClientOrderId - The unique order id
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._get('order', True, data=params)

    def get_all_orders(self, **params):
        """
        Get all account orders; active, canceled, or filled.
        https://www.binance.com/restapipub.html#all-orders-signed
        :param params:
            symbol - required
            orderId - The unique order id
            limit - Default 500; max 500.
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._get('allOrders', True, data=params)

    def cancel_order(self, **params):
        """
        Cancel an active order.
        https://www.binance.com/restapipub.html#all-orders-signed
        :param params:
            symbol - required
            orderId - If orderId is set, it will get orders >= that orderId. Otherwise most recent orders are returned.
            origClientOrderId - The unique order id
            newClientOrderId - The unique order id
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._delete('order', True, data=params)

    def get_open_orders(self, **params):
        """
        Get all open orders on a symbol.
        https://www.binance.com/restapipub.html#current-open-orders-signed
        :param params:
            symbol - required
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._get('openOrders', True, data=params)

    # User Stream Endpoints
    def get_account(self, **params):
        """
        Get all account orders; active, canceled, or filled.
        https://www.binance.com/restapipub.html#account-information-signed
        :param params:
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._get('account', True, data=params)

    def get_my_trades(self, **params):
        """
        Get trades for a specific account and symbol.
        https://www.binance.com/restapipub.html#account-trade-list-signed
        :param params:
            symbol - required
            limit - Default 500; max 500.
            fromId - TradeId to fetch from. Default gets most recent trades.
            recvWindow - the number of milliseconds the request is valid for
        :return:
        """
        return self._get('myTrades', True, data=params)
