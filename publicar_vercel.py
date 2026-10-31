#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publica en Vercel la vista de CONSULTA del Consolidado (solo lectura).
  - Calcula el consolidado desde el histórico local (balance_historico.db).
  - Genera vercel_consolidado/public/ (página + datos/consolidado.json).
  - Despliega con la CLI de Vercel a producción (URL fija *.vercel.app).
No envía credenciales de Odoo ni el Excel: solo el consolidado ya calculado.

Uso:
    python publicar_vercel.py                  # genera y publica
    python publicar_vercel.py --solo-generar   # genera sin publicar (prueba local)
    python publicar_vercel.py --configurar-clave  # crea/cambia la clave del visor y publica
"""

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
os.chdir(RAIZ)

import consolidado_core  # noqa: E402

DIR_VERCEL = RAIZ / "vercel_consolidado"
DIR_PUBLIC = DIR_VERCEL / "public"
ARCHIVO_CLAVE = RAIZ / "CLAVE_VERCEL.txt"
USUARIO_VISOR = "gerencia"


def _vercel_cmd() -> list:
    exe = shutil.which("vercel") or shutil.which("vercel.cmd")
    if not exe:
        npm_global = Path(os.environ.get("APPDATA", "")) / "npm" / "vercel.cmd"
        if npm_global.exists():
            exe = str(npm_global)
    if not exe:
        sys.exit("No se encontró la CLI de Vercel (npm install -g vercel)")
    return [exe]


def _vercel(*args, entrada: str = None) -> subprocess.CompletedProcess:
    return subprocess.run(_vercel_cmd() + list(args), cwd=DIR_VERCEL, input=entrada,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def generar() -> Path:
    """Escribe la página estática y el JSON con todo el histórico consolidado."""
    datos = consolidado_core.calcular("0000-01-01", date.today().isoformat())
    datos["generado"] = datetime.now().isoformat(timespec="seconds")

    (DIR_PUBLIC / "datos").mkdir(parents=True, exist_ok=True)
    (DIR_PUBLIC / "datos" / "consolidado.json").write_text(
        json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    html = (RAIZ / "templates" / "consolidado.html").read_text(encoding="utf-8")
    html = re.sub(r"<!-- solo-local -->.*?<!-- /solo-local -->\n?", "", html, flags=re.S)
    html = html.replace("<title>Consolidado · Balance Grupo de Empresas</title>",
                        "<title>Consolidado · Balance (consulta)</title>")
    html = html.replace('<script src="/static/consolidado.js"></script>',
                        '<script>window.FUENTE_ESTATICA = "datos/consolidado.json";</script>\n'
                        '<script src="consolidado.js"></script>')
    if "{{" in html:
        raise RuntimeError("Quedó una variable de plantilla sin reemplazar en la página de Vercel")
    (DIR_PUBLIC / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(RAIZ / "static" / "consolidado.js", DIR_PUBLIC / "consolidado.js")
    print(f"Generado: {len(datos['fechas'])} día(s) en {DIR_PUBLIC}")
    return DIR_PUBLIC


def configurar_clave() -> None:
    """Crea una clave nueva para el visor; en Vercel queda solo su hash."""
    clave = secrets.token_urlsafe(12)
    hash_hex = hashlib.sha256(clave.encode("utf-8")).hexdigest()
    for nombre, valor in (("VISOR_USUARIO", USUARIO_VISOR), ("VISOR_CLAVE_SHA256", hash_hex)):
        _vercel("env", "rm", nombre, "production", "--yes")
        r = _vercel("env", "add", nombre, "production", entrada=valor)
        if r.returncode != 0:
            sys.exit(f"No se pudo guardar {nombre} en Vercel:\n{r.stderr[-800:]}")
    ARCHIVO_CLAVE.write_text(
        f"Visor Consolidado en Vercel\nusuario: {USUARIO_VISOR}\nclave: {clave}\n", encoding="utf-8")
    print(f"Clave del visor creada. Está en {ARCHIVO_CLAVE} (no se muestra aquí).")


def publicar() -> str:
    r = _vercel("deploy", "--prod", "--yes")
    if r.returncode != 0:
        sys.exit(f"Falló el despliegue en Vercel:\n{(r.stderr or r.stdout)[-1500:]}")
    salida = r.stdout + r.stderr
    alias = re.findall(r"Aliased:?\s+(https://\S+)", salida)
    urls = re.findall(r"https://[a-z0-9.-]+\.vercel\.app", salida)
    url = (alias or urls or ["(ver en vercel.com)"])[-1]
    (RAIZ / "logs").mkdir(exist_ok=True)
    with open(RAIZ / "logs" / "vercel.log", "a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  publicado {url}\n")
    print(f"Publicado: {url}")
    return url


if __name__ == "__main__":
    args = set(sys.argv[1:])
    generar()
    if "--solo-generar" in args:
        sys.exit(0)
    if "--configurar-clave" in args:
        # El proyecto debe existir antes de poder guardarle variables de entorno
        if not (DIR_VERCEL / ".vercel" / "project.json").exists():
            r = _vercel("link", "--yes", "--project", "balance-consolidado")
            if r.returncode != 0:
                sys.exit(f"No se pudo crear/enlazar el proyecto:\n{(r.stderr or r.stdout)[-800:]}")
        configurar_clave()
    publicar()
