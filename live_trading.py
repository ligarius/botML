"""Live trading module using Binance REST API and shared risk logic."""

import time
import hmac
import hashlib
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import requests

from botml.risk import PositionSizer, RiskManager
from botml.utils import load_config, setup_logging

CONFIG = load_config()
LOGGER = setup_logging(CONFIG, __name__)

BINANCE_URL = CONFIG.get('api_url', 'https://api.binance.com')
API_KEY = CONFIG.get('api_key')
API_SECRET = CONFIG.get('api_secret')


class BinanceClient:
    """Minimal Binance REST API client for order execution with retries."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = BINANCE_URL):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url
        self.retry_attempts = CONFIG.get('retry_attempts', 3)
        self.retry_backoff = CONFIG.get('retry_backoff', 1.0)
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-MBX-APIKEY': api_key})

    def reconnect(self) -> None:
        """Create a new HTTP session."""
        self.session.close()
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'X-MBX-APIKEY': self.api_key})

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Perform a request with retry logic."""
        for attempt in range(1, self.retry_attempts + 1):
            try:
                resp = self.session.request(method, self.base_url + endpoint, timeout=10, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                if attempt == self.retry_attempts:
                    raise
                time.sleep(self.retry_backoff * attempt)
                self.reconnect()

    def _sign_params(self, params: dict) -> dict:
        query = urlencode(params)
        signature = hmac.new(self.api_secret, query.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        return params

    def create_order(self, **params):
        params.setdefault('timestamp', int(time.time() * 1000))
        signed = self._sign_params(params)
        try:
            response = self._request('post', '/api/v3/order', params=signed)
        except requests.RequestException as exc:
            raise RuntimeError(f"Order request failed: {exc}") from exc
        return response.json()

    def get_symbol_min_notional(self, symbol: str) -> float:
        """Return the minimum notional value for a symbol."""
        try:
            resp = self._request('get', '/api/v3/exchangeInfo', params={'symbol': symbol})
        except requests.RequestException as exc:
            raise RuntimeError(f"exchangeInfo request failed: {exc}") from exc
        data = resp.json()
        try:
            filters = data['symbols'][0]['filters']
            for f in filters:
                if f.get('filterType') == 'MIN_NOTIONAL':
                    return float(f['minNotional'])
        except (KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"Invalid exchangeInfo response: {exc}") from exc
        raise RuntimeError('MIN_NOTIONAL filter not found')


@dataclass
class Trade:
    entry_price: float
    direction: str  # 'long' or 'short'
    size: float
    stop: float
    take_profit: float


class LiveTrader:
    """Execute trades on Binance using risk management utilities."""

    def __init__(self, symbol: str, account_size: float,
                 client: Optional[BinanceClient] = None,
                 risk_manager: Optional[RiskManager] = None,
                 sizer: Optional[PositionSizer] = None,
                 open_trades_file: Optional[str] = None):
        self.symbol = symbol
        self.account_size = account_size
        self.client = client or BinanceClient(API_KEY, API_SECRET)
        self.sizer = sizer or PositionSizer(account_size)
        self.risk_manager = risk_manager or RiskManager(account_size)
        self.open_trades = []
        self.open_trades_file = open_trades_file or CONFIG.get('open_trades_file', 'open_trades.json')

    def reconnect(self) -> None:
        """Reconnect the Binance client."""
        self.client.reconnect()

    def resume(self) -> None:
        """Resume trading after a connection drop."""
        self.reconnect()

    def open_trade(self, price: float, direction: str = "long", bracket: bool = False) -> Optional[Trade]:
        stop = self.risk_manager.stop_loss_price(price, direction)
        take_profit = self.risk_manager.take_profit_price(price, direction)
        size = self.sizer.size_from_stop(price, stop)
        side = 'BUY' if direction == 'long' else 'SELL'
        try:
            min_notional = self.client.get_symbol_min_notional(self.symbol)
        except Exception as exc:
            LOGGER.warning("Could not fetch minNotional for %s: %s", self.symbol, exc)
            min_notional = 0.0

        order_value = size * price
        if min_notional and order_value < min_notional:
            LOGGER.info(
                "Order value %.8f below minimum %.8f for %s - skipping",
                order_value,
                min_notional,
                self.symbol,
            )
            return None

        self.client.create_order(symbol=self.symbol, side=side, type='MARKET', quantity=size)
        trade = Trade(price, direction, size, stop, take_profit)
        self.open_trades.append(trade)
        try:
            import json
            with open(self.open_trades_file, 'w') as fh:
                json.dump([t.__dict__ for t in self.open_trades], fh)
        except Exception:
            pass
        if bracket:
            opposite = 'SELL' if direction == 'long' else 'BUY'
            try:
                self.client.create_order(
                    symbol=self.symbol,
                    side=opposite,
                    type='STOP_MARKET',
                    stopPrice=stop,
                    closePosition='true'
                )
            except Exception:
                pass
            try:
                self.client.create_order(
                    symbol=self.symbol,
                    side=opposite,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=take_profit,
                    closePosition='true'
                )
            except Exception:
                pass
        return trade

    def update_equity(self, equity: float) -> bool:
        """Update equity and enforce max drawdown."""
        return self.risk_manager.update_equity(equity)
