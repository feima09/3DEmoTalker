import httpx

httpx_client = httpx.AsyncClient(
    timeout=30,
    http2=True,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)
