"""OpenSubtitles REST client."""
import json
import urllib.request
import urllib.error

BASE = "https://api.opensubtitles.com/api/v1/"

def api(route, key, payload=None, token=''):
    headers = {'Api-Key': key, 'User-Agent': 'LegendasLinux v1.0', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + route, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        errors = {401: 'Credenciais inválidas.', 403: 'Acesso negado: confira a chave e a conta.', 406: 'Limite de downloads atingido.', 429: 'Muitas requisições. Tente mais tarde.'}
        raise RuntimeError(errors.get(e.code, f'OpenSubtitles retornou HTTP {e.code}.')) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Não foi possível conectar ao OpenSubtitles. Confira a internet e tente novamente.') from None


