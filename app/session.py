import requests
import requests.adapters


def build_session(pool_size: int = 100) -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
