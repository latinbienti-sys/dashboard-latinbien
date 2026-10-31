#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Núcleo del balance del grupo de empresas (LB, GR, JV).
Configuración de la hoja, mapeo de filas/columnas y funciones para
leer / actualizar / reportar sin acoplarse al servidor web.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from openpyxl import load_workbook

# --- Configuración general ---
EXCEL_FILE = "BALANCE GRUPO DE EMPRESAS.xlsx"
SHEET_NAME = "Copia de BALANCE 3"
BACKUP_DIR = "backups_balance"

# Fila (1-based) de cada concepto en la hoja "Copia de BALANCE 3"
ROW_MAP: Dict[str, int] = {
    # ACTIVO
    "relacion_saldos": 7,
    "inventario": 8,
    "fondo_ahorro": 9,
    "fondo_caja": 10,
    "inventario_transito": 11,
    "cxc_empresas": 12,
    "cxc_tec": 13,
    "cxc_moto": 14,
    "marca": 15,
    "saldo_td": 16,
    "sistema_admin": 17,
    "total_activo": 18,
    # PASIVO
    "pasivo": 19,
    "tdc_gr_2025": 20,
    "tdc_gr_2026": 21,
    "anticipo_tec": 22,
    "anticipo_moto": 23,
    "cxp_op": 24,
    "cxp_tec": 25,
    "cxp_moto": 26,
    "prestamo_bdv": 27,
    "total_pasivo": 28,
    "activo_menos_pasivo": 29,
}

# Columnas (1-based) de cada empresa y campos auxiliares
COLS: Dict[str, int] = {
    "lb": 7,        # G
    "gr": 9,        # I
    "jv": 11,       # K
    "brecha": 11,   # K (BRECHA %)
    "origen": 13,   # M (ORIGEN DATO)
    "valor_ref": 5, # E
}

# Celdas de cabecera (fila, columna)
HEADER = {
    "fecha_corte": (2, 5),   # E2
    "tasa_bcv": (3, 7),      # G3
    "tasa_binance": (3, 9),  # I3
    "brecha": (3, 11),       # K3
}

ACTIVO_ROWS = [
    "relacion_saldos", "inventario", "fondo_ahorro", "fondo_caja",
    "inventario_transito", "cxc_empresas", "cxc_tec", "cxc_moto",
    "marca", "saldo_td", "sistema_admin",
]
PASIVO_ROWS = [
    "tdc_gr_2025", "tdc_gr_2026", "anticipo_tec", "anticipo_moto",
    "cxp_op", "cxp_tec", "cxp_moto", "prestamo_bdv",
]


def _num(value: Any) -> float:
    """Devuelve un float seguro (None / vacíos -> 0.0)."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def recalcular_totales(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Suma en Python los subtotales a partir de las filas mostradas."""
    def sumar(rows: List[Dict[str, Any]]) -> Dict[str, float]:
        return {
            "lb": round(sum(_num(r.get("lb")) for r in rows), 2),
            "gr": round(sum(_num(r.get("gr")) for r in rows), 2),
            "jv": round(sum(_num(r.get("jv")) for r in rows), 2),
        }

    ta = sumar(datos.get("activo", []))
    tp = sumar(datos.get("pasivo", []))
    neto = {k: round(ta[k] - tp[k], 2) for k in ("lb", "gr", "jv")}
    return {"total_activo": ta, "total_pasivo": tp, "activo_menos_pasivo": neto}


def leer_datos() -> Dict[str, Any]:
    """Lee el balance del Excel y devuelve activo, pasivo, totales e info."""
    if not Path(EXCEL_FILE).exists():
        raise FileNotFoundError(f"No existe el archivo {EXCEL_FILE}")

    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb[SHEET_NAME]

    datos: Dict[str, Any] = {"info": {}, "activo": [], "pasivo": [], "totales": {}}

    fecha = ws.cell(*HEADER["fecha_corte"]).value
    if hasattr(fecha, "strftime"):
        fecha = fecha.strftime("%Y-%m-%d")
    datos["info"]["fecha_corte"] = fecha
    datos["info"]["tasa_bcv"] = ws.cell(*HEADER["tasa_bcv"]).value
    datos["info"]["tasa_binance"] = ws.cell(*HEADER["tasa_binance"]).value
    datos["info"]["brecha"] = ws.cell(*HEADER["brecha"]).value

    for key, row in ROW_MAP.items():
        if key in ("total_activo", "total_pasivo", "activo_menos_pasivo", "pasivo"):
            continue
        concepto = ws.cell(row, 2).value or key
        origen = ws.cell(row, COLS["origen"]).value
        fila = {
            "key": key,
            "concepto": str(concepto).strip(),
            "lb": ws.cell(row, COLS["lb"]).value,
            "gr": ws.cell(row, COLS["gr"]).value,
            "jv": ws.cell(row, COLS["jv"]).value,
            "origen": str(origen).strip().upper() if origen else "",
            "fila": row,
        }
        if key in ACTIVO_ROWS:
            datos["activo"].append(fila)
        if key in PASIVO_ROWS:
            datos["pasivo"].append(fila)

    datos["totales"] = recalcular_totales(datos)
    wb.close()
    return datos


def guardar_valores(fila: int, lb: float, gr: float, jv: float, origen: str) -> None:
    """Actualiza una fila del balance y su origen, preservando fórmulas."""
    wb = load_workbook(EXCEL_FILE, data_only=False)
    ws = wb[SHEET_NAME]
    ws.cell(fila, COLS["lb"]).value = float(lb or 0)
    ws.cell(fila, COLS["gr"]).value = float(gr or 0)
    ws.cell(fila, COLS["jv"]).value = float(jv or 0)
    if origen:
        ws.cell(fila, COLS["origen"]).value = str(origen).strip().upper()
    wb.save(EXCEL_FILE)
    wb.close()


def guardar_tasas(tasa_bcv: Optional[float], tasa_binance: Optional[float], brecha: Optional[float]) -> None:
    """Escribe las tasas del día (BCV, Binance y brecha) en la cabecera del Excel."""
    wb = load_workbook(EXCEL_FILE, data_only=False)
    ws = wb[SHEET_NAME]
    if tasa_bcv is not None:
        ws.cell(*HEADER["tasa_bcv"]).value = float(tasa_bcv)
    if tasa_binance is not None:
        ws.cell(*HEADER["tasa_binance"]).value = float(tasa_binance)
    if brecha is not None:
        ws.cell(*HEADER["brecha"]).value = round(float(brecha), 4)
    wb.save(EXCEL_FILE)
    wb.close()


def crear_backup() -> str:
    """Crea una copia fechada del archivo y devuelve la ruta."""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = Path(BACKUP_DIR) / f"BALANCE_GRUPO_EMPRESAS_{ts}.xlsx"
    shutil.copy2(EXCEL_FILE, dst)
    return str(dst)


def reporte() -> Dict[str, Any]:
    """Reporte resumen simple del período actual del Excel."""
    datos = leer_datos()
    return {
        "fecha_corte": datos["info"].get("fecha_corte"),
        "tasa_bcv": datos["info"].get("tasa_bcv"),
        "tasa_binance": datos["info"].get("tasa_binance"),
        "brecha_pct": datos["info"].get("brecha"),
        "total_activo": datos["totales"]["total_activo"],
        "total_pasivo": datos["totales"]["total_pasivo"],
        "activo_menos_pasivo": datos["totales"]["activo_menos_pasivo"],
        "generado": datetime.now().isoformat(timespec="seconds"),
    }
