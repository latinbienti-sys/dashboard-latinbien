#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtención automática de tasas de cambio (Venezuela):
  - BCV  : tasa oficial (fuente: ve.dolarapi.com -> "oficial")
  - Binance: USDT/VES tomado del P2P público de Binance (promedio de los mejores anuncios)
La brecha % se calcula como ((binance - bcv) / bcv) * 100.
"""

import json
import ssl
import urllib.request
from datetime import datetime
from typing import Dict, Any, Optional

DOLARAPI_OFICIAL = "https://ve.dolarapi.com/v1/dolares/oficial"
BINANCE_P2P = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
TIMEOUT = 20
_SSL = ssl.create_default_context()


def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url: str, payload: Dict[str, Any]) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL) as r:
        return json.loads(r.read().decode("utf-8"))


def obtener_tasa_bcv() -> Optional[float]:
    """Tasa oficial BCV (Bs por USD)."""
    try:
        d = _get(DOLARAPI_OFICIAL)
        return float(d.get("promedio"))
    except Exception:
        return None


def obtener_tasa_binance(trade_type: str = "SELL", rows: int = 5) -> Optional[float]:
    """Precio USDT/VES en Binance P2P (promedio de los mejores 'rows' anuncios)."""
    try:
        payload = {
            "asset": "USDT", "fiat": "VES", "merchantCheck": True,
            "page": 1, "rows": rows, "tradeType": trade_type, "payTypes": [],
        }
        d = _post(BINANCE_P2P, payload)
        precios = [
            float(a["adv"]["price"])
            for a in d.get("data", [])
            if a.get("adv", {}).get("price")
        ]
        if not precios:
            return None
        return round(sum(precios) / len(precios), 4)
    except Exception:
        return None


def calcular_brecha(bcv: Optional[float], binance: Optional[float]) -> Optional[float]:
    """Brecha % entre la tasa Binance y la oficial BCV."""
    if not bcv or not binance:
        return None
    return round((binance - bcv) / bcv * 100, 4)


def obtener_tasas() -> Dict[str, Any]:
    """Devuelve BCV, Binance y brecha junto con la marca de tiempo."""
    bcv = obtener_tasa_bcv()
    binance = obtener_tasa_binance()
    return {
        "tasa_bcv": bcv,
        "tasa_binance": binance,
        "brecha": calcular_brecha(bcv, binance),
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
    }


if __name__ == "__main__":
    print(json.dumps(obtener_tasas(), indent=2, ensure_ascii=False))
