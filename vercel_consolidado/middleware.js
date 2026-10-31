// Protege TODO el sitio (página y datos) con usuario y clave (HTTP Basic).
// La clave no está en el código: Vercel guarda solo su hash SHA-256 en
// las variables de entorno VISOR_USUARIO y VISOR_CLAVE_SHA256.
// Si faltan, el sitio queda cerrado (nunca abierto por error).
import { next } from "@vercel/functions";
import { createHash, timingSafeEqual } from "node:crypto";

export const config = { runtime: "nodejs" };

const pedirClave = () =>
    new Response("Acceso restringido", {
        status: 401,
        headers: { "WWW-Authenticate": 'Basic realm="Consolidado Balance", charset="UTF-8"', "Cache-Control": "no-store" },
    });

const sha256 = (txt) => createHash("sha256").update(txt, "utf8").digest();

export default function middleware(request) {
    const usuario = process.env.VISOR_USUARIO;
    const hashClave = process.env.VISOR_CLAVE_SHA256;
    if (!usuario || !hashClave) {
        return new Response("Sitio no configurado", { status: 503, headers: { "Cache-Control": "no-store" } });
    }

    const auth = request.headers.get("authorization") || "";
    if (!auth.startsWith("Basic ")) return pedirClave();
    let u = "", c = "";
    try {
        const dec = Buffer.from(auth.slice(6), "base64").toString("utf8");
        const i = dec.indexOf(":");
        u = dec.slice(0, i);
        c = dec.slice(i + 1);
    } catch {
        return pedirClave();
    }
    const okUsuario = timingSafeEqual(sha256(u), sha256(usuario));
    const okClave = timingSafeEqual(sha256(c), Buffer.from(hashClave, "hex"));
    if (!(okUsuario && okClave)) return pedirClave();
    return next();
}
