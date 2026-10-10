
import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from db import get_connection

password_hasher = PasswordHasher()


def register_user(name, email, password):
    name = name.strip()
    email = email.strip().lower()

    if not name:
        raise ValueError("Please enter your name.")

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Please enter a valid email address.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    password_hash = password_hasher.hash(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, 'user')
                ON CONFLICT (email) DO NOTHING
                RETURNING user_id
                """,
                (name, email, password_hash),
            )
            result = cur.fetchone()

            if result is None:
                raise ValueError("This email is already registered.")

            return result[0]


def login_user(email, password):
    email = email.strip().lower()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, name, email, password_hash, role
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            user = cur.fetchone()

    if user is None:
        return None

    try:
        password_hasher.verify(user[3], password)
    except (VerifyMismatchError, VerificationError):
        return None

    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[4],
    }