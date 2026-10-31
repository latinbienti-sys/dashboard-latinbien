#!/usr/bin/env python3
"""Servidor local del Embudo de Ventas -> http://127.0.0.1:8080

Sirve la carpeta del proyecto con cabeceras anti-cache para que el
auto-refresco del frontend lea siempre el cache_live.json mas reciente.
Solo escucha en 127.0.0.1 (no expone nada hacia la red local).
"""
import http.server
import os
import socketserver
import sys
import threading
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
PUERTO = int(os.environ.get('PUERTO_EMBUDO', '8080'))
URL = 'http://127.0.0.1:%d/' % PUERTO


class Manejador(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write('[serve] %s\n' % (fmt % args))


class Servidor(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

    try:
        httpd = Servidor(('127.0.0.1', PUERTO), Manejador)
    except OSError:
        # Puerto ocupado: probablemente ya hay una instancia sirviendo.
        import urllib.request
        try:
            urllib.request.urlopen(URL, timeout=2)
            print('[serve] Ya hay una instancia corriendo en %s' % URL)
            webbrowser.open(URL)
            return 0
        except Exception:
            print('[serve] ERROR: el puerto %d esta ocupado por otro servicio.' % PUERTO)
            print('[serve] Cierre esa aplicacion y reintente.')
            return 1

    print('[serve] Embudo de Ventas disponible en %s' % URL)
    print('[serve] Ctrl+C para detener.')
    threading.Timer(1.0, lambda: webbrowser.open(URL)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n[serve] Detenido.')
    finally:
        httpd.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
