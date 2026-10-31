#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usuarios y roles del balance.
  - gerencia : ve todo el balance (ERP + WS + totales) y puede editar todo.
  - captura  : personal externo; solo ve y registra los conceptos de origen WS.

Los usuarios se guardan en usuarios_balance.json con la clave hasheada.
Administración por consola:
    python auth_balance.py crear  <usuario> <gerencia|captura>
    python auth_balance.py borrar <usuario>
    python auth_balance.py listar
"""

import json
import os
import secrets
import sys
from functools import wraps
from getpass import getpass
from pathlib import Path
from typing import Dict, Any, Optional

from flask import session, jsonify, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash

USERS_FILE = "usuarios_balance.json"
SECRET_FILE = ".balance_secret"
ROLES = ("gerencia", "captura")


def secret_key() -> str:
    """Clave de sesión persistente (se genera una sola vez)."""
    p = Path(SECRET_FILE)
    if not p.exists():
        p.write_text(secrets.token_hex(32), encoding="utf-8")
    return p.read_text(encoding="utf-8").strip()


def _cargar() -> Dict[str, Any]:
    p = Path(USERS_FILE)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _guardar(users: Dict[str, Any]) -> None:
    Path(USERS_FILE).write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def hay_usuarios() -> bool:
    return bool(_cargar())


def verificar(usuario: str, clave: str) -> Optional[str]:
    """Devuelve el rol si usuario/clave son correctos, si no None."""
    u = _cargar().get((usuario or "").strip().lower())
    if u and check_password_hash(u["hash"], clave or ""):
        return u["rol"]
    return None


def crear_usuario(usuario: str, clave: str, rol: str) -> None:
    if rol not in ROLES:
        raise ValueError(f"Rol inválido: {rol} (use {', '.join(ROLES)})")
    users = _cargar()
    users[usuario.strip().lower()] = {"hash": generate_password_hash(clave), "rol": rol}
    _guardar(users)


def usuario_actual() -> Optional[str]:
    return session.get("usuario")


def rol_actual() -> Optional[str]:
    return session.get("rol")


def requiere_rol(*roles):
    """Protege una ruta: sin sesión -> login (o 401 en /api); rol no permitido -> 403."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            rol = rol_actual()
            es_api = request.path.startswith("/api/")
            if not rol:
                if es_api:
                    return jsonify({"error": "Sesión no iniciada"}), 401
                return redirect(url_for("login", next=request.path))
            if rol not in roles:
                if es_api:
                    return jsonify({"error": "No autorizado para esta acción"}), 403
                return redirect(url_for("inicio"))
            return fn(*args, **kwargs)
        return wrapper
    return deco


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["listar"]:
        for nombre, u in _cargar().items():
            print(f"{nombre:20} {u['rol']}")
    elif args[:1] == ["crear"] and len(args) == 3:
        clave = getpass("Clave: ")
        if clave != getpass("Repita la clave: "):
            sys.exit("Las claves no coinciden")
        if len(clave) < 8:
            sys.exit("La clave debe tener al menos 8 caracteres")
        crear_usuario(args[1], clave, args[2])
        print(f"Usuario '{args[1]}' creado con rol {args[2]}")
    elif args[:1] == ["borrar"] and len(args) == 2:
        users = _cargar()
        if users.pop(args[1].strip().lower(), None) is None:
            sys.exit("No existe ese usuario")
        _guardar(users)
        print(f"Usuario '{args[1]}' eliminado")
    else:
        print(__doc__)
