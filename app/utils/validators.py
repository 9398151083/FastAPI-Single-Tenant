# ┌────────────────────────────── FIELD VALIDATIONS ──────────────────────────────────────────┐


def validate_password(password: str) -> str:
    """
    Custom password validation to ensure it meets security standards.
    """
    field_name = "Password"

    if not any(char.isupper() for char in password):
        raise ValueError(f"{field_name} ")
    if not any(char.islower() for char in password):
        raise ValueError(f"{field_name}")
    if not any(char.isdigit() for char in password):
        raise ValueError(f"{field_name} ")
    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
        raise ValueError(f"{field_name} ")
    if " " in password:
        raise ValueError(f"{field_name} ")

    return password
