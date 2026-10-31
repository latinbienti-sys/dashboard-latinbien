#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Almacén histórico diario del balance (SQLite).
Guarda, por cada fecha, las tasas del día y los valores de cada concepto
(LB, GR, JV) con su origen de dato.
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = "balance_historico.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS dias (
                fecha        TEXT PRIMARY KEY,
                tasa_bcv     REAL,
                tasa_binance REAL,
                brecha       REAL,
                actualizado  TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS valores (
                fecha    TEXT,
                fila     INTEGER,
                key      TEXT,
                concepto TEXT,
                lb       REAL,
                gr       REAL,
                jv       REAL,
                origen   TEXT,
                PRIMARY KEY (fecha, fila)
            )
        """)
        # Auditoría: quién registró el valor y cuándo (migración en BD existentes)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(valores)")}
        if "usuario" not in cols:
            c.execute("ALTER TABLE valores ADD COLUMN usuario TEXT")
        if "registrado" not in cols:
            c.execute("ALTER TABLE valores ADD COLUMN registrado TEXT")


def guardar_dia(fecha: str, valores: List[Dict[str, Any]], tasas: Optional[Dict[str, Any]] = None,
                usuario: Optional[str] = None) -> None:
    """Inserta/actualiza una fecha completa (tasas + valores por concepto)."""
    tasas = tasas or {}
    with _conn() as c:
        c.execute(
            """INSERT INTO dias(fecha, tasa_bcv, tasa_binance, brecha, actualizado)
               VALUES(?,?,?,?,?)
               ON CONFLICT(fecha) DO UPDATE SET
                   tasa_bcv=excluded.tasa_bcv,
                   tasa_binance=excluded.tasa_binance,
                   brecha=excluded.brecha,
                   actualizado=excluded.actualizado""",
            (fecha, tasas.get("tasa_bcv"), tasas.get("tasa_binance"),
             tasas.get("brecha"), datetime.now().isoformat(timespec="seconds")),
        )
        for v in valores:
            c.execute(
                """INSERT INTO valores(fecha, fila, key, concepto, lb, gr, jv, origen, usuario, registrado)
                   VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(fecha, fila) DO UPDATE SET
                       key=excluded.key, concepto=excluded.concepto,
                       lb=excluded.lb, gr=excluded.gr, jv=excluded.jv, origen=excluded.origen,
                       usuario=COALESCE(valores.usuario, excluded.usuario),
                       registrado=COALESCE(valores.registrado, excluded.registrado)""",
                (fecha, int(v["fila"]), v.get("key"), v.get("concepto"),
                 float(v.get("lb") or 0), float(v.get("gr") or 0),
                 float(v.get("jv") or 0), v.get("origen"),
                 usuario, datetime.now().isoformat(timespec="seconds")),
            )


def guardar_valor_fila(fecha: str, fila: int, lb: float, gr: float, jv: float, origen: str,
                       usuario: Optional[str] = None, key: Optional[str] = None,
                       concepto: Optional[str] = None) -> None:
    """Actualiza (upsert) una sola fila de una fecha, sin tocar las demás."""
    with _conn() as c:
        c.execute(
            """INSERT INTO dias(fecha, actualizado) VALUES(?,?)
               ON CONFLICT(fecha) DO UPDATE SET actualizado=excluded.actualizado""",
            (fecha, datetime.now().isoformat(timespec="seconds")),
        )
        c.execute(
            """INSERT INTO valores(fecha, fila, key, concepto, lb, gr, jv, origen, usuario, registrado)
               VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(fecha, fila) DO UPDATE SET
                   key=COALESCE(excluded.key, valores.key),
                   concepto=COALESCE(excluded.concepto, valores.concepto),
                   lb=excluded.lb, gr=excluded.gr, jv=excluded.jv, origen=excluded.origen,
                   usuario=excluded.usuario, registrado=excluded.registrado""",
            (fecha, int(fila), key, concepto, float(lb or 0), float(gr or 0), float(jv or 0),
             origen, usuario, datetime.now().isoformat(timespec="seconds")),
        )


def existe_dia(fecha: str) -> bool:
    with _conn() as c:
        return c.execute("SELECT 1 FROM dias WHERE fecha=?", (fecha,)).fetchone() is not None


def obtener_dia(fecha: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        dia = c.execute("SELECT * FROM dias WHERE fecha=?", (fecha,)).fetchone()
        if not dia:
            return None
        vals = c.execute("SELECT * FROM valores WHERE fecha=? ORDER BY fila", (fecha,)).fetchall()
        return {"fecha": fecha, "tasas": dict(dia), "valores": [dict(v) for v in vals]}


def listar_dias() -> List[Dict[str, Any]]:
    """Lista de fechas registradas (más reciente primero)."""
    with _conn() as c:
        rows = c.execute("SELECT * FROM dias ORDER BY fecha DESC").fetchall()
        return [dict(r) for r in rows]


def fecha_anterior(fecha: str) -> Optional[str]:
    """Devuelve la fecha registrada inmediatamente anterior a la indicada."""
    with _conn() as c:
        row = c.execute(
            "SELECT fecha FROM dias WHERE fecha < ? ORDER BY fecha DESC LIMIT 1", (fecha,)
        ).fetchone()
        return row["fecha"] if row else None
