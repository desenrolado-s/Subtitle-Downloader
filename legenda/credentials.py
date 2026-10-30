"""Store credentials exclusively in the Linux Secret Service vault."""
import json

SERVICE = 'io.github.desenrolado_s.Legenda'
ACCOUNT = 'opensubtitles'


def backend():
    from keyring.backends.SecretService import Keyring
    return Keyring()


def load():
    raw = backend().get_password(SERVICE, ACCOUNT)
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) for k in ('key', 'user', 'password')):
        raise ValueError('Invalid stored credentials')
    return data


def save(key, user, password):
    backend().set_password(SERVICE, ACCOUNT, json.dumps(dict(key=key, user=user, password=password)))


def forget():
    vault = backend()
    if vault.get_password(SERVICE, ACCOUNT) is not None:
        vault.delete_password(SERVICE, ACCOUNT)
