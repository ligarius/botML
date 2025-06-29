"""Live trading module using Binance REST API and shared risk logic."""

import time
import hmac
import hashlib
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import requests

from risk import PositionSizer, RiskManager
from utils import load_config, setup_logging

CONFIG = load_config()
setup_logging(CONFIG)

BINANCE_URL = CONFIG.get('api_url', 'https://api.binance.com')
API_KEY = CONFIG.get('api_key')
API_SECRET = CONFIG.get('api_secret')


class BinanceClient:
    """Minimal Binance REST API client for order execution."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = BINANCE_URL):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-MBX-APIKEY': api_key})

    def _sign_params(self, params: dict) -> dict:
        query = urlencode(params)
        signature = hmac.new(self.api_secret, query.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        return params

    def create_order(self, **params):
        params.setdefault('timestamp', int(time.time() * 1000))
        signed = self._sign_params(params)
        response = self.session.post(self.base_url + '/api/v3/order', params=signed, timeout=10)
        response.raise_for_status()
        return response.json()


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
                 sizer: Optional[PositionSizer] = None):
        self.symbol = symbol
        self.account_size = account_size
        self.client = client or BinanceClient(API_KEY, API_SECRET)
        self.sizer = sizer or PositionSizer(account_size)
        self.risk_manager = risk_manager or RiskManager(account_size)
        self.open_trades = []

    def open_trade(self, price: float, direction: str = "long") -> Trade:
        stop = self.risk_manager.stop_loss_price(price, direction)
        take_profit = self.risk_manager.take_profit_price(price, direction)
        size = self.sizer.size_from_stop(price, stop)
        side = 'BUY' if direction == 'long' else 'SELL'
        order = self.client.create_order(symbol=self.symbol, side=side, type='MARKET', quantity=size)
        trade = Trade(price, direction, size, stop, take_profit)
        self.open_trades.append(trade)
        return trade

    def update_equity(self, equity: float) -> bool:
        """Update equity and enforce max drawdown."""
        return self.risk_manager.update_equity(equity)
