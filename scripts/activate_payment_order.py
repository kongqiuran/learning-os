import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import create_database_tables
from src.services.payment_order_service import activate_payment_order


def main():
    parser = argparse.ArgumentParser(description="Activate a pending manual payment order.")
    parser.add_argument("--order-no", required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    create_database_tables()
    entitlement = activate_payment_order(args.order_no, operator_note=args.note or None)
    print(
        f"Payment order {args.order_no} is active as entitlement "
        f"{entitlement.id} until {entitlement.expires_at.isoformat()}."
    )


if __name__ == "__main__":
    main()
