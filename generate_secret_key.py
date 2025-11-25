"""Generate a secure SECRET_KEY for Flask sessions.

Run this script to generate a random secret key:
    python generate_secret_key.py

Copy the output to your .env file:
    SECRET_KEY=<generated_key>
"""
import secrets

if __name__ == "__main__":
    secret_key = secrets.token_hex(32)
    print("=" * 60)
    print("Generated SECRET_KEY for Flask:")
    print("=" * 60)
    print(f"\nSECRET_KEY={secret_key}\n")
    print("=" * 60)
    print("Copy the line above to your .env file")
    print("=" * 60)
