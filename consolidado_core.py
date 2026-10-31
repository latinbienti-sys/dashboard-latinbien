#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidado del grupo (LB + GR + JV) por día, a partir del histórico local.
Lo usan la pestaña Consolidado (app_balance.py) y el publicador a Vercel.
"""

from typing import Dict, Any

import balance_core as core
import historico


def base_num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def calcular(desde: str, hasta: str) -> Dict[str, Any]:
    """Serie diaria consolidada de cada concepto y de los totales.
    Si un concepto no se registró un día, se arrastra el último valor conocido
    y se marca como 'arrastrado'."""

    base = core.leer_datos()
    conceptos = [dict(f, grupo="activo") for f in base["activo"]] + \
                [dict(f, grupo="pasivo") for f in base["pasivo"]]
    ultimo = {}  # fila -> (lb, gr, jv)
    fechas, tasas_bcv = [], []
    series = {c["fila"]: {"lb": [], "gr": [], "jv": [], "total": [], "arrastrado": []} for c in conceptos}

    for d in sorted(historico.listar_dias(), key=lambda x: x["fecha"]):
        if d["fecha"] > hasta:
            break
        dia = historico.obtener_dia(d["fecha"])
        hoy_vals = {v["fila"]: v for v in dia["valores"]}
        for fila, v in hoy_vals.items():
            ultimo[fila] = (base_num(v["lb"]), base_num(v["gr"]), base_num(v["jv"]))
        if d["fecha"] < desde:
            continue
        fechas.append(d["fecha"])
        tasas_bcv.append(d.get("tasa_bcv"))
        for c in conceptos:
            s = series[c["fila"]]
            val = ultimo.get(c["fila"])
            for i, k in enumerate(("lb", "gr", "jv")):
                s[k].append(val[i] if val else None)
            s["total"].append(round(sum(val), 2) if val else None)
            s["arrastrado"].append(c["fila"] not in hoy_vals and val is not None)

    def sumar(filas):
        out = {k: [] for k in ("lb", "gr", "jv", "total")}
        for i in range(len(fechas)):
            for k in out:
                out[k].append(round(sum(series[f][k][i] or 0 for f in filas), 2))
        return out

    f_act = [c["fila"] for c in conceptos if c["grupo"] == "activo"]
    f_pas = [c["fila"] for c in conceptos if c["grupo"] == "pasivo"]
    activo, pasivo = sumar(f_act), sumar(f_pas)
    neto = {k: [round(a - p, 2) for a, p in zip(activo[k], pasivo[k])] for k in activo}

    return {
        "desde": desde, "hasta": hasta, "fechas": fechas, "tasa_bcv": tasas_bcv,
        "conceptos": [
            {"key": c["key"], "concepto": c["concepto"], "grupo": c["grupo"],
             "origen": c["origen"], **series[c["fila"]]}
            for c in conceptos
        ],
        "totales": {"activo": activo, "pasivo": pasivo, "neto": neto},
    }
