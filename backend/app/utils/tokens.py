import secrets

def generate_token() -> str:
    return "tk_" + secrets.token_hex(24)