"""Create an API key for external agents (CoWork, N8N, etc).

Usage:
    DATABASE_URL="postgresql://user:pass@host/db" python scripts/create_api_key.py

The script will:
1. Find your admin user in the database
2. Generate a secure API key (avk_...)
3. Insert it with the specified scopes
4. Print the raw key ONCE -- copy it immediately
"""

import hashlib
import os
import secrets
import sys
import uuid

import psycopg2


def generate_api_key():
    """Generate API key matching app/core/api_key_auth.py logic."""
    random_part = secrets.token_urlsafe(32)
    raw_key = f"avk_{random_part}"[:36]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    return raw_key, key_hash, key_prefix


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set.")
        print('Usage: DATABASE_URL="postgresql://..." python scripts/create_api_key.py')
        sys.exit(1)

    # Normalize URL for psycopg2
    url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"

    conn = psycopg2.connect(url)
    cur = conn.cursor()

    # Find admin user
    cur.execute("SELECT id, email, role FROM users WHERE role = 'ADMIN' AND is_active = true")
    admins = cur.fetchall()

    if not admins:
        print("ERROR: No active ADMIN user found in database.")
        print("Available users:")
        cur.execute("SELECT id, email, role, is_active FROM users LIMIT 10")
        for row in cur.fetchall():
            print(f"  {row[1]} (role={row[2]}, active={row[3]})")
        cur.close()
        conn.close()
        sys.exit(1)

    admin_id, admin_email, _ = admins[0]
    print(f"Using admin user: {admin_email}")

    # Generate key
    raw_key, key_hash, key_prefix = generate_api_key()

    key_name = "CoWork Agent"
    scopes = [
        "autosourcing:read",
        "autosourcing:write",
        "autosourcing:job_read",
        "daily_review:read",
    ]

    key_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name, scopes, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, true, NOW(), NOW())
        """,
        (key_id, admin_id, key_hash, key_prefix, key_name, psycopg2.extras.Json(scopes)),
    )

    conn.commit()
    cur.close()
    conn.close()

    print()
    print("=" * 60)
    print("  API KEY CREATED SUCCESSFULLY")
    print("=" * 60)
    print()
    print(f"  Name:   {key_name}")
    print(f"  Scopes: {', '.join(scopes)}")
    print(f"  Prefix: {key_prefix}")
    print()
    print(f"  KEY: {raw_key}")
    print()
    print("  IMPORTANT: Copy this key NOW.")
    print("  It will NEVER be shown again.")
    print()
    print("  Usage:")
    print(f'  curl -H "X-API-Key: {raw_key}" \\')
    print("    https://arbitragevault-backend-v2.onrender.com/api/v1/autosourcing/jobs")
    print("=" * 60)


if __name__ == "__main__":
    import psycopg2.extras  # noqa: F811
    main()
