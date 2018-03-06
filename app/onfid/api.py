from onfido import Api

from config import ONFIDO_TOKEN
from session import build_session

api = Api(ONFIDO_TOKEN)

session = build_session(1024)


def get_href(href: str) -> dict:
    res = session.get(
        href if 'https://' in href else f'https://api.onfido.com{href}',
        headers={'Authorization': f'Token token={ONFIDO_TOKEN}', 'Accept': 'application/json'},
    )
    return res.json()
