# -*- coding: utf-8 -*-
"""
Exploracion del CRM de Odoo (latinbienmotors.com) - SOLO LECTURA / CONSULTA.

Lista: bases de datos disponibles, modelos de CRM, etiquetas, etapas
y campos existentes en crm.lead (para conocer monto total, aprobado, plazo, fecha aprobacion).
"""
import json
import os
import sys
import urllib.request
import http.cookiejar

BASE = os.environ.get("ODOO_BASE", "https://latinbienmotors.com")
DB = os.environ.get("ODOO_DB", "latinbien")
USER = os.environ.get("ODOO_USER", "")
PWD = os.environ.get("ODOO_PASSWORD", "")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def rpc(url, method, params):
    payload = {"jsonrpc": "2.0", "method": "call", "params": params, "id": 1}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = opener.open(req, timeout=90)
    return json.loads(resp.read().decode())


def call_kw(model, method, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    res = rpc(BASE + "/web/dataset/call_kw", model, {
        "model": model, "method": method, "args": args, "kwargs": kwargs
    })
    if "error" in res:
        raise RuntimeError(json.dumps(res["error"], ensure_ascii=False)[:2000])
    return res["result"]


def main():
    if not USER or not PWD:
        print("ERROR: Faltan ODOO_USER / ODOO_PASSWORD")
        sys.exit(1)

    print("== Autenticando en", BASE, "db:", DB)
    auth = rpc(BASE + "/web/session/authenticate", "call", {
        "db": DB, "login": USER, "password": PWD
    })
    r = auth.get("result", {})
    if not r.get("uid"):
        print("Fallo de autenticacion:")
        print(json.dumps(auth, ensure_ascii=False)[:500])
        sys.exit(1)
    print("OK uid:", r.get("uid"), "| user:", r.get("name"), "| db:", r.get("db"))

    # ---- crm.stage (etapas del pipeline) ----
    print("\n== crm.stage (etapas) ==")
    stages = call_kw("crm.stage", "search_read", [[]], {"fields": ["id", "name", "sequence", "is_won", "team_id", "fold"], "order": "sequence"})
    for s in stages:
        print(json.dumps({k: s[k] for k in ["id", "name", "sequence", "is_won", "team_id", "fold"]}, ensure_ascii=False))

    # ---- crm.tag (etiquetas) ----
    print("\n== crm.tag (etiquetas) ==")
    tags = call_kw("crm.tag", "search_read", [[]], {"fields": ["id", "name"], "order": "name"})
    for t in tags:
        print(t["id"], "|", t["name"])

    # ---- campos de crm.lead ----
    print("\n== campos de crm.lead (todas) ==")
    try:
        fields = call_kw("crm.lead", "fields_get", [], {"attributes": ["string", "type", "store"]})
        interesting = {}
        for fname, fmeta in fields.items():
            s = (fmeta.get("string") or "").lower()
            # Campos custom x_ y campos financieros clave
            if fname.startswith("x_") or any(k in s for k in ["monto", "moneda", "precio", "plazo", "aprob", "cuota", "inicial", "banco", "financ", "marca", "modelo", "vehic", "nota", "tag", "etiqueta", "responsible", "fecha", "pago", "credito", "interes", "tasa"]):
                interesting[fname] = {"string": fmeta.get("string"), "type": fmeta.get("type"), "store": fmeta.get("store")}
        for fname, m in sorted(interesting.items()):
            print(f"{fname} | {m['string']} | {m['type']} | store={m['store']}")
    except RuntimeError as e:
        print("fields_get error:", e)

    # ---- buscar leads con algunas etiquetas ----
    print("\n== crm.lead: primeras 10 oportunidades, con tags ==")
    leads = call_kw("crm.lead", "search_read", [[]], {
        "fields": ["id", "name", "partner_id", "contact_name", "email_from", "stage_id", "tag_ids", "expected_revenue", "user_id", "team_id", "date_open", "date_deadline", "date_last_stage_update", "description", "x_montototal", "x_monto_aprobado", "x_plazo", "x_fecha_aprobacion"],
        "limit": 10
    })
    for l in leads:
        print(json.dumps(l, ensure_ascii=False, default=str)[:800])


if __name__ == "__main__":
    main()