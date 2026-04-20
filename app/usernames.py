import secrets

from wonderwords import RandomWord

_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
_SUFFIX_LEN = 4
_rw = RandomWord()


def generate_username() -> str:
    adj = _rw.word(include_parts_of_speech=["adjective"]).lower()
    noun = _rw.word(include_parts_of_speech=["noun"]).lower()
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(_SUFFIX_LEN))
    return f"{adj}-{noun}-{suffix}"
