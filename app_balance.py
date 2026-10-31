#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor web (Flask) para el BALANCE GRUPO DE EMPRESAS.
  - Tablero diario navegable por fecha (histórico en SQLite).
  - Tasas automáticas: BCV y Binance P2P, con brecha %.
  - Registro/actualización de valores por popup.
  - Reporte de variación vs. el día anterior.
  - Backup y descarga del Excel.
Odoo queda intacto: solo existe un punto de consulta futura (inactivo).
"""

import os
import json
import subprocess
import sys
import threading
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for


def _cargar_env(ruta: str = "name.env") -> None:
    """Carga variables KEY=VALOR de name.env (ODOO_USER, ODOO_PASS...) si no están ya definidas."""
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


os.chdir(os.path.dirname(os.path.abspath(__file__)))
_cargar_env()

import auth_balance as auth
from auth_balance import requiere_rol
import balance_core as core
import consolidado_core
import historico
import tasas
import odoo_erp
from balance_core import EXCEL_FILE, ROW_MAP, COLS, ACTIVO_ROWS, PASIVO_ROWS

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.secret_key = auth.secret_key()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(hours=10))

# Modo público (detrás de Cloudflare Tunnel con HTTPS): BALANCE_PUBLICO=1
PUBLICO = os.environ.get("BALANCE_PUBLICO") == "1"
if PUBLICO:
    app.config["SESSION_COOKIE_SECURE"] = True

# Bloqueo de login: MAX_INTENTOS fallidos por IP+usuario bloquean durante BLOQUEO.
MAX_INTENTOS = 5
BLOQUEO = timedelta(minutes=15)
_fallos: dict = {}


def _ip_cliente() -> str:
    # Con el túnel, la IP real llega en CF-Connecting-IP (el servidor solo escucha en localhost).
    if PUBLICO:
        return request.headers.get("CF-Connecting-IP") or request.remote_addr or ""
    return request.remote_addr or ""


@app.after_request
def _cabeceras_seguridad(resp):
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    if PUBLICO:
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return resp

# Conceptos que registra el personal externo (rol "captura"): los de origen WS.
CAPTURA_KEYS = ["relacion_saldos", "fondo_ahorro", "fondo_caja", "saldo_td", "tdc_gr_2026"]
CAPTURA_FILAS = {ROW_MAP[k]: k for k in CAPTURA_KEYS}

historico.init_db()


def _consultar_odoo(key: str, fecha: str = "") -> dict:
    """Consulta SOLO LECTURA a Odoo (nunca escribe en el ERP).
    Si falla (credenciales, red, permisos) lo reporta sin romper el flujo."""
    try:
        return odoo_erp.consultar(key, fecha or None)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def _serializar_tasas(t: dict) -> dict:
    """Convierte fechas/hora a texto para devolver por JSON."""
    return {k: v for k, v in t.items()}


# ------------------------- Sesión -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if not auth.hay_usuarios():
        error = "No hay usuarios creados. Ejecute: python auth_balance.py crear <usuario> gerencia"
    elif request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip().lower()
        clave_intento = (_ip_cliente(), usuario)
        n, desde = _fallos.get(clave_intento, (0, datetime.now()))
        if n >= MAX_INTENTOS and datetime.now() - desde < BLOQUEO:
            error = "Demasiados intentos fallidos. Intente de nuevo en 15 minutos."
            return render_template("login.html", error=error), 429
        rol = auth.verificar(usuario, request.form.get("clave"))
        if rol:
            _fallos.pop(clave_intento, None)
            session.clear()
            session.permanent = True
            session["usuario"], session["rol"] = usuario, rol
            return redirect(url_for("inicio"))
        _fallos[clave_intento] = (1 if n >= MAX_INTENTOS else n + 1, datetime.now())
        error = "Usuario o clave incorrectos"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------- Rutas web -------------------------
@app.route("/")
def inicio():
    rol = auth.rol_actual()
    if rol == "gerencia":
        return render_template("index.html", usuario=auth.usuario_actual())
    if rol == "captura":
        return redirect(url_for("captura"))
    return redirect(url_for("login"))


# ------------------------- Captura externa (solo WS) -------------------------
def _conceptos_captura() -> dict:
    base = core.leer_datos()
    return {f["fila"]: f["concepto"] for f in base["activo"] + base["pasivo"] if f["fila"] in CAPTURA_FILAS}


@app.route("/captura")
@requiere_rol("captura", "gerencia")
def captura():
    return render_template("captura.html", usuario=auth.usuario_actual())


@app.route("/api/captura/datos")
@requiere_rol("captura", "gerencia")
def api_captura_datos():
    """Solo los conceptos WS del día: el personal externo no recibe nada más."""
    fecha = request.args.get("fecha") or date.today().isoformat()
    hist = historico.obtener_dia(fecha)
    mapa = {v["fila"]: v for v in (hist["valores"] if hist else [])}
    filas = []
    for fila, concepto in _conceptos_captura().items():
        v = mapa.get(fila)
        filas.append({
            "fila": fila, "key": CAPTURA_FILAS[fila], "concepto": concepto,
            "lb": v["lb"] if v else None, "gr": v["gr"] if v else None, "jv": v["jv"] if v else None,
            "registrado": bool(v), "usuario": v.get("usuario") if v else None,
            "actualizado": v.get("registrado") if v else None,
        })
    return jsonify({"fecha": fecha, "filas": filas})


@app.route("/api/captura/guardar", methods=["POST"])
@requiere_rol("captura", "gerencia")
def api_captura_guardar():
    data = request.get_json(force=True, silent=True) or {}
    try:
        fila = int(data.get("fila"))
        lb, gr, jv = (float(data.get(k) or 0) for k in ("lb", "gr", "jv"))
    except (TypeError, ValueError):
        return jsonify({"error": "Fila o valores numéricos inválidos"}), 400
    if fila not in CAPTURA_FILAS:
        return jsonify({"error": "Este concepto no se registra desde captura"}), 403

    hoy = date.today()
    try:
        f = date.fromisoformat(data.get("fecha") or hoy.isoformat())
    except ValueError:
        return jsonify({"error": "Fecha inválida"}), 400
    # El personal externo solo puede registrar hoy o hasta 7 días atrás
    if auth.rol_actual() == "captura" and not (hoy - timedelta(days=7) <= f <= hoy):
        return jsonify({"error": "Solo puede registrar fechas de los últimos 7 días"}), 403

    try:
        historico.guardar_valor_fila(f.isoformat(), fila, lb, gr, jv, "WS",
                                     usuario=auth.usuario_actual(), key=CAPTURA_FILAS[fila],
                                     concepto=_conceptos_captura().get(fila))
        if f == hoy:
            core.guardar_valores(fila, lb, gr, jv, "WS")
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True, "msg": "Registro guardado correctamente"})


@app.route("/api/datos")
@requiere_rol("gerencia")
def api_datos():
    """Datos del día seleccionado. Si el día está guardado en el histórico,
    devuelve ese snapshot; si no, la estructura actual del Excel (base)."""
    fecha = request.args.get("fecha") or date.today().isoformat()
    try:
        base = core.leer_datos()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    hist = historico.obtener_dia(fecha)
    guardado = hist is not None

    if hist:
        mapa = {v["fila"]: v for v in hist["valores"]}
        for grupo in ("activo", "pasivo"):
            for f in base[grupo]:
                v = mapa.get(f["fila"])
                if v:
                    f["lb"], f["gr"], f["jv"], f["origen"] = (
                        v["lb"], v["gr"], v["jv"], v.get("origen") or f["origen"],
                    )
                    f["usuario"], f["registrado"] = v.get("usuario"), v.get("registrado")
                    f["en_dia"] = True
        # No pisar las tasas con vacío cuando el día se creó desde captura
        for k in ("tasa_bcv", "tasa_binance", "brecha"):
            if hist["tasas"].get(k) is not None:
                base["info"][k] = hist["tasas"][k]

    base["info"]["fecha_corte"] = fecha
    base["fecha"] = fecha
    base["guardado"] = guardado
    base["totales"] = core.recalcular_totales(base)
    base["usuario"] = auth.usuario_actual()
    base["captura_pendiente"] = [
        f["concepto"] for f in base["activo"] + base["pasivo"]
        if f["fila"] in CAPTURA_FILAS and not f.get("en_dia")
    ]
    return jsonify(base)


@app.route("/api/tasas")
@requiere_rol("gerencia")
def api_tasas():
    """Obtiene (o refresca) las tasas del día de forma automática."""
    t = tasas.obtener_tasas()
    if t["tasa_binance"] is not None and t["tasa_bcv"] is not None:
        try:
            core.guardar_tasas(t["tasa_bcv"], t["tasa_binance"], t["brecha"])
        except Exception:  # noqa: BLE001
            pass
    return jsonify(_serializar_tasas(t))


@app.route("/api/historico")
@requiere_rol("gerencia")
def api_historico():
    dias = historico.listar_dias()
    if not dias:
        return jsonify([])
    # Agregar totales de cada día para mostrarlos en la tabla histórica
    resultado = []
    for d in dias:
        dia = historico.obtener_dia(d["fecha"])
        if dia:
            rows = {v["fila"]: v for v in dia["valores"]}
            datos = core.leer_datos()
            for grupo in ("activo", "pasivo"):
                for f in datos[grupo]:
                    v = rows.get(f["fila"])
                    if v:
                        f["lb"], f["gr"], f["jv"] = v["lb"], v["gr"], v["jv"]
            tot = core.recalcular_totales(datos)
            d["total_activo"] = tot["total_activo"]
            d["total_pasivo"] = tot["total_pasivo"]
        resultado.append(d)
    return jsonify(resultado)


@app.route("/consolidado")
@requiere_rol("gerencia")
def consolidado():
    return render_template("consolidado.html", usuario=auth.usuario_actual())


@app.route("/api/consolidado")
@requiere_rol("gerencia")
def api_consolidado():
    """Serie diaria consolidada (LB + GR + JV) de cada concepto y de los totales."""
    hasta = request.args.get("hasta") or date.today().isoformat()
    desde = request.args.get("desde") or (date.fromisoformat(hasta) - timedelta(days=60)).isoformat()
    return jsonify(consolidado_core.calcular(desde, hasta))


@app.route("/api/guardar", methods=["POST"])
@requiere_rol("gerencia")
def api_guardar():
    """Guarda un valor: actualiza el Excel y registra el día en el histórico."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        fila = int(data.get("fila"))
        lb = float(data.get("lb") or 0)
        gr = float(data.get("gr") or 0)
        jv = float(data.get("jv") or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Fila o valores numéricos inválidos"}), 400

    fecha = data.get("fecha") or date.today().isoformat()
    origen = str(data.get("origen", "MANUAL")).strip().upper()

    try:
        core.guardar_valores(fila, lb, gr, jv, origen)
        historico.guardar_valor_fila(fecha, fila, lb, gr, jv, origen, usuario=auth.usuario_actual())
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True, "msg": "Registro guardado correctamente", "fecha": fecha})


@app.route("/api/guardar_dia", methods=["POST"])
@requiere_rol("gerencia")
def api_guardar_dia():
    """Guarda un día completo (todos los conceptos + tasas) en el histórico."""
    data = request.get_json(force=True, silent=True) or {}
    fecha = data.get("fecha") or date.today().isoformat()
    valores = data.get("valores") or []
    t = data.get("tasas") or {}

    if not valores:
        return jsonify({"error": "No hay valores que guardar"}), 400

    try:
        t = {
            "tasa_bcv": t.get("tasa_bcv") or None,
            "tasa_binance": t.get("tasa_binance") or None,
            "brecha": t.get("brecha") or None,
        }
        historico.guardar_dia(fecha, valores, t, usuario=auth.usuario_actual())
        # Sincronizar también el Excel (si es el día de hoy se guardan las tasas)
        if fecha == date.today().isoformat() and t["tasa_bcv"]:
            try:
                core.guardar_tasas(t["tasa_bcv"], t["tasa_binance"], t["brecha"])
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    _publicar_vercel_en_segundo_plano()
    return jsonify({"ok": True, "msg": f"Día {fecha} guardado correctamente"})


_lock_vercel = threading.Lock()


def _publicar_vercel_en_segundo_plano() -> None:
    """Actualiza el visor de consulta en Vercel sin hacer esperar al usuario.
    Solo si el proyecto ya fue enlazado (vercel_consolidado/.vercel) y no hay otra publicación en curso."""
    if not os.path.exists(os.path.join("vercel_consolidado", ".vercel", "project.json")):
        return
    if not _lock_vercel.acquire(blocking=False):
        return

    def correr():
        try:
            os.makedirs("logs", exist_ok=True)
            with open(os.path.join("logs", "vercel.log"), "a", encoding="utf-8") as log:
                subprocess.run([sys.executable, "publicar_vercel.py"], stdout=log, stderr=log, timeout=600)
        except Exception:  # noqa: BLE001
            pass
        finally:
            _lock_vercel.release()

    threading.Thread(target=correr, daemon=True).start()


@app.route("/api/reporte")
@requiere_rol("gerencia")
def api_reporte():
    """Reporte del día con variación vs. el día anterior registrado."""
    fecha = request.args.get("fecha") or date.today().isoformat()
    dia = historico.obtener_dia(fecha)

    if not dia:
        # Día sin guardar: usar lo que hay en el Excel como base
        base = core.leer_datos()
        valores = [
            {"fila": f["fila"], "key": f["key"], "concepto": f["concepto"],
             "lb": base_num(f["lb"]), "gr": base_num(f["gr"]), "jv": base_num(f["jv"]),
             "origen": f["origen"]}
            for f in base["activo"] + base["pasivo"]
        ]
        tasas_dia = {
            "tasa_bcv": base["info"].get("tasa_bcv"),
            "tasa_binance": base["info"].get("tasa_binance"),
            "brecha": base["info"].get("brecha"),
        }
    else:
        valores = dia["valores"]
        tasas_dia = dict(dia["tasas"]) if dia["tasas"] else {}

    totales = _totales_desde(valores)
    fecha_anterior = historico.fecha_anterior(fecha)
    variacion = None
    if fecha_anterior:
        dia_ant = historico.obtener_dia(fecha_anterior)
        if dia_ant:
            tot_ant = _totales_desde(dia_ant["valores"])
            variacion = {
                "fecha": fecha_anterior,
                "total_activo": _dif(totales["total_activo"], tot_ant["total_activo"]),
                "total_pasivo": _dif(totales["total_pasivo"], tot_ant["total_pasivo"]),
                "activo_menos_pasivo": _dif(totales["activo_menos_pasivo"], tot_ant["activo_menos_pasivo"]),
            }

    return jsonify({
        "fecha": fecha,
        "guardado": dia is not None,
        "tasas": {
            "tasa_bcv": tasas_dia.get("tasa_bcv"),
            "tasa_binance": tasas_dia.get("tasa_binance"),
            "brecha": tasas_dia.get("brecha"),
        },
        "totales": totales,
        "variacion": variacion,
        "detalle": valores,
        "generado": datetime.now().isoformat(timespec="seconds"),
    })


def base_num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _totales_desde(valores: list) -> dict:
    """Reconstruye totales desde una lista de valores guardados."""
    activo = [v for v in valores if v.get("fila") in [ROW_MAP[k] for k in ACTIVO_ROWS]]
    pasivo = [v for v in valores if v.get("fila") in [ROW_MAP[k] for k in PASIVO_ROWS]]
    return core.recalcular_totales({
        "activo": activo,
        "pasivo": pasivo,
    })


def _dif(a: dict, b: dict) -> dict:
    return {k: round(base_num(a.get(k)) - base_num(b.get(k)), 2) for k in ("lb", "gr", "jv")}


@app.route("/api/backup")
@requiere_rol("gerencia")
def api_backup():
    try:
        ruta = core.crear_backup()
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True, "archivo": ruta})


@app.route("/api/consultar_erp", methods=["POST"])
@requiere_rol("gerencia")
def api_consultar_erp():
    """Consulta (SOLO LECTURA) de un concepto del balance contra Odoo/ERP.
    Devuelve lb/gr/jv cuando hay consulta definida."""
    data = request.get_json(force=True, silent=True) or {}
    key = data.get("key", "")
    fecha = data.get("fecha", "") or request.args.get("fecha", "")
    return jsonify(_consultar_odoo(key, fecha))


@app.route("/api/descargar")
@requiere_rol("gerencia")
def api_descargar():
    if not os.path.exists(EXCEL_FILE):
        return jsonify({"error": "Archivo no encontrado"}), 404
    return send_file(EXCEL_FILE, as_attachment=True)


if __name__ == "__main__":
    # Sin debug por defecto: el depurador de Werkzeug permite ejecutar código desde la red.
    # Para desarrollo local: set BALANCE_DEBUG=1
    if PUBLICO:
        # Producción: waitress solo en localhost; Cloudflare Tunnel publica con HTTPS.
        from waitress import serve
        print("Balance en modo público: http://127.0.0.1:5000 (expuesto vía Cloudflare Tunnel)")
        serve(app, host="127.0.0.1", port=5000, threads=8)
    else:
        app.run(host="0.0.0.0", port=5000, debug=os.environ.get("BALANCE_DEBUG") == "1")