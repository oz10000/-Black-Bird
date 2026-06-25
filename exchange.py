# exchange.py
# ============================================================
# CLIENTE OKX V5 PARA FUTUROS (SWAP)
# BASADO EN EL VERIFICADOR PYDROID (v9)
# CORRECCIÓN: posSide OBLIGATORIO para todas las órdenes de futuros
# ============================================================

import time
import json
import hmac
import hashlib
import base64
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from telemetry import telemetry
from config import MAX_RETRIES_PER_ORDER, ORDER_TIMEOUT, SYNC_TIME_ENABLED

class Exchange:
    def __init__(self, api_key: str, secret_key: str, passphrase: str, demo: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.demo = demo
        self.base_url = "https://www.okx.com"
        self.session = requests.Session()
        self._connected = False
        self._time_offset = 0
        self._last_sync_time = 0
        self._sync_interval = 30  # Segundos

    # ============================================================
    # 1. SINCRONIZACIÓN HORARIA (ROBUSTA)
    # ============================================================

    def _iso_timestamp(self) -> str:
        """Timestamp en formato ISO 8601 (requerido por OKX V5)."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def _sync_time(self, force: bool = False) -> bool:
        """Obtiene el timestamp del servidor y calcula el offset."""
        now = time.time()
        if not force and (now - self._last_sync_time) < self._sync_interval:
            return True
        try:
            resp = self.session.get(f"{self.base_url}/api/v5/public/time", timeout=5)
            data = resp.json()
            if data.get("code") == "0":
                server_ts = int(data['data'][0]['ts'])
                local_ts = int(time.time() * 1000)
                self._time_offset = server_ts - local_ts
                self._last_sync_time = now
                telemetry.log_debug("exchange", f"Sincronización horaria: offset={self._time_offset}ms")
                return True
        except Exception as e:
            telemetry.log_error("exchange", f"Error en _sync_time: {e}")
        return False

    def _ensure_sync(self):
        """Asegura que el timestamp esté sincronizado antes de firmar."""
        self._sync_time()

    # ============================================================
    # 2. FIRMA Y PETICIONES (CON REINTENTO 50102)
    # ============================================================

    def _sign_request(self, method: str, path: str, params: Dict = None, body: Dict = None) -> tuple:
        """
        Firma la petición según OKX V5.
        Devuelve (headers, body_str).
        """
        self._ensure_sync()

        timestamp = self._iso_timestamp()
        if body:
            body_str = json.dumps(body, separators=(",", ":"))
        else:
            body_str = ""

        if params:
            query = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            full_path = f"{path}?{query}"
        else:
            full_path = path

        # Cadena a firmar: timestamp + method + path + body
        sign_str = timestamp + method + full_path + body_str
        signature = base64.b64encode(
            hmac.new(self.secret_key.encode(), sign_str.encode(), hashlib.sha256).digest()
        ).decode()

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }
        # Modo demo (simulación)
        if self.demo:
            headers["x-simulated-trading"] = "1"

        return headers, body_str

    def _handle_response(self, response: requests.Response) -> Dict:
        """Procesa la respuesta de OKX."""
        try:
            data = response.json()
        except:
            return {"ok": False, "error": "Invalid JSON response"}

        # OKX devuelve "code": "0" para éxito, "sMsg" para mensajes de orden
        if data.get("code") != "0":
            msg = data.get("msg", "Unknown error")
            # Algunos endpoints usan "sMsg" dentro de los datos
            if "sMsg" in data:
                msg = data["sMsg"]
            return {"ok": False, "error": msg, "raw": data}

        return {"ok": True, "data": data.get("data", [])}

    def _request_with_retry(self, method: str, path: str, params: Dict = None, body: Dict = None) -> Dict:
        """
        Ejecuta la petición con reintento automático en caso de error 50102 (timestamp expirado).
        """
        headers, body_str = self._sign_request(method, path, params, body)

        try:
            if method == "GET":
                resp = self.session.get(
                    f"{self.base_url}{path}",
                    headers=headers,
                    params=params,
                    timeout=ORDER_TIMEOUT
                )
            else:
                resp = self.session.post(
                    f"{self.base_url}{path}",
                    headers=headers,
                    data=body_str,
                    timeout=ORDER_TIMEOUT
                )
        except requests.exceptions.Timeout:
            return {"ok": False, "error": "Timeout"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

        result = self._handle_response(resp)

        # Si falla por timestamp expirado, resincronizar y reintentar una vez
        if not result.get("ok") and "50102" in str(result.get("raw", {}).get("code", "")):
            telemetry.log_warning("exchange", "Error 50102 detectado, resincronizando y reintentando")
            self._sync_time(force=True)
            # Reintentar sin posibilidad de bucle infinito
            headers2, body_str2 = self._sign_request(method, path, params, body)
            if method == "GET":
                resp2 = self.session.get(f"{self.base_url}{path}", headers=headers2, params=params, timeout=ORDER_TIMEOUT)
            else:
                resp2 = self.session.post(f"{self.base_url}{path}", headers=headers2, data=body_str2, timeout=ORDER_TIMEOUT)
            return self._handle_response(resp2)

        return result

    # ============================================================
    # 3. CONEXIÓN
    # ============================================================

    def connect(self) -> bool:
        """Verifica la conexión y sincroniza el tiempo."""
        try:
            self._sync_time(force=True)
            resp = self.session.get(f"{self.base_url}/api/v5/public/time", timeout=10)
            data = resp.json()
            if data.get("code") == "0":
                self._connected = True
                telemetry.log_info("exchange", "Conectado a OKX correctamente")
                return True
        except Exception as e:
            telemetry.log_error("exchange", f"Error en connect: {e}")
        return False

    # ============================================================
    # 4. CUENTA Y BALANCE
    # ============================================================

    def get_balance(self) -> Dict:
        """Obtiene el balance de la cuenta."""
        if not self._connected:
            return {"ok": False, "error": "No conectado"}
        return self._request_with_retry("GET", "/api/v5/account/balance")

    # ============================================================
    # 5. POSICIONES
    # ============================================================

    def get_positions(self, symbol: Optional[str] = None) -> Dict:
        """Obtiene las posiciones abiertas. Si symbol es None, devuelve todas."""
        if not self._connected:
            return {"ok": False, "error": "No conectado"}
        params = {}
        if symbol:
            params["instId"] = symbol
        return self._request_with_retry("GET", "/api/v5/account/positions", params=params)

    # ============================================================
    # 6. ÓRDENES DE MERCADO (CON posSide)
    # ============================================================

    def place_market_order(self, symbol: str, side: str, size: float) -> Dict:
        """
        Abre una orden de mercado en futuros.
        - side: 'buy' (Long) o 'sell' (Short)
        - size: cantidad de contratos
        """
        if not self._connected:
            return {"ok": False, "error": "No conectado"}

        pos_side = "long" if side.lower() == "buy" else "short"
        body = {
            "instId": symbol,
            "tdMode": "cross",
            "side": side.lower(),
            "posSide": pos_side,      # OBLIGATORIO para futuros SWAP
            "ordType": "market",
            "sz": str(size),
        }
        telemetry.log_debug("exchange", f"Market order: {symbol} {side} size={size} posSide={pos_side}")
        return self._request_with_retry("POST", "/api/v5/trade/order", body=body)

    # ============================================================
    # 7. ÓRDENES CONDICIONADAS (TP/SL) (CON posSide)
    # ============================================================

    def place_algo_order(self, symbol: str, side: str, trigger_price: float, order_price: float, size: float, order_type: str = "conditional") -> Dict:
        """
        Coloca una orden condicionada (Take Profit o Stop Loss).
        - side: 'buy' o 'sell' (dirección de la orden condicionada)
        - trigger_price: precio que activa la orden
        - order_price: precio de ejecución (-1 para mercado)
        """
        if not self._connected:
            return {"ok": False, "error": "No conectado"}

        pos_side = "long" if side.lower() == "buy" else "short"
        # Usamos 'trigger' para TP/SL (OKX lo acepta)
        body = {
            "instId": symbol,
            "tdMode": "cross",
            "side": side.lower(),
            "posSide": pos_side,      # OBLIGATORIO
            "ordType": "trigger",     # 'conditional' también funciona, pero 'trigger' es más simple
            "sz": str(size),
            "triggerPx": str(trigger_price),
            "orderPx": str(order_price),
            "triggerPxType": "last",
        }
        telemetry.log_debug("exchange", f"Algo order: {symbol} {side} trigger={trigger_price} order={order_price}")
        return self._request_with_retry("POST", "/api/v5/trade/order-algo", body=body)

    # ============================================================
    # 8. TRAILING STOP (CON posSide)
    # ============================================================

    def place_trailing_order(self, symbol: str, side: str, size: float, callback_rate: float) -> Dict:
        """
        Coloca un trailing stop nativo.
        - callback_rate: porcentaje de trailing (ej. 0.008 = 0.8%)
        """
        if not self._connected:
            return {"ok": False, "error": "No conectado"}

        pos_side = "long" if side.lower() == "buy" else "short"
        body = {
            "instId": symbol,
            "tdMode": "cross",
            "side": side.lower(),
            "posSide": pos_side,      # OBLIGATORIO
            "ordType": "move_order_stop",
            "sz": str(size),
            "callbackRatio": str(callback_rate),
        }
        telemetry.log_debug("exchange", f"Trailing order: {symbol} {side} callback={callback_rate}")
        return self._request_with_retry("POST", "/api/v5/trade/order-algo", body=body)

    # ============================================================
    # 9. CANCELACIONES
    # ============================================================

    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancela una orden de mercado/limit normal."""
        if not self._connected:
            return {"ok": False, "error": "No conectado"}
        body = {"ordId": order_id, "instId": symbol}
        return self._request_with_retry("POST", "/api/v5/trade/cancel-order", body=body)

    def cancel_algo_order(self, algo_id: str, symbol: str) -> Dict:
        """Cancela una orden algorítmica (TP/SL/Trailing)."""
        if not self._connected:
            return {"ok": False, "error": "No conectado"}
        # OKX requiere lista de objetos para cancelar algoritmos
        body = [{"algoId": algo_id, "instId": symbol}]
        return self._request_with_retry("POST", "/api/v5/trade/cancel-algos", body=body)

    # ============================================================
    # 10. CONSULTA DE ÓRDENES PENDIENTES
    # ============================================================

    def get_pending_algo_orders(self, symbol: Optional[str] = None) -> Dict:
        """Obtiene órdenes algorítmicas pendientes (TP/SL/Trailing)."""
        if not self._connected:
            return {"ok": False, "error": "No conectado"}
        params = {"ordType": "trigger,move_order_stop"}
        if symbol:
            params["instId"] = symbol
        return self._request_with_retry("GET", "/api/v5/trade/orders-algo-pending", params=params)
