"""Promote a user to admin. Usage: uv run python scripts/make_admin.py <email>"""
import sys
from sqlmodel import Session, select

from app.core.database import engine
from app.models.user import User
from app.models.currency import Currency  # noqa: F401 — register FK for display_currency_id


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run python scripts/make_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            print(f"User not found: {email}")
            sys.exit(1)

        user.role = "admin"
        session.add(user)
        session.commit()
        print(f"✓ {user.email} → {user.role}")


if __name__ == "__main__":
    main()