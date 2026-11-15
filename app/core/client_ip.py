"""IP del visitante para los límites de intentos (D62).

Publicado, el frontend llega a la API por un proxy (función de Cloudflare
Pages) y la IP de la conexión es la del proxy: todos los visitantes
compartirían un mismo límite. El proxy reenvía la IP real en `X-Client-IP`
junto con `X-Proxy-Secret`; solo si la clave coincide con PROXY_SECRET se
cree esa IP. Sin clave (desarrollo o llamada directa) se usa la conexión.
"""

import secrets

from fastapi import Request

from app.core.config import get_settings


def client_key(request: Request) -> str:
    secret = get_settings().proxy_secret.get_secret_value()
    sent = request.headers.get("x-proxy-secret", "")
    if secret and sent and secrets.compare_digest(sent.encode(), secret.encode()):
        forwarded = request.headers.get("x-client-ip", "").strip()
        if forwarded:
            return forwarded[:64]
    return request.client.host if request.client else "desconocido"
