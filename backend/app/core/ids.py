import secrets

# no 0/O/1/I/L to avoid confusion when users type the comment by hand
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def public_id(prefix: str, length: int = 6) -> str:
    return f"{prefix}-" + "".join(secrets.choice(ALPHABET) for _ in range(length))
