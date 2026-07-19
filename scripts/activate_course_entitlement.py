import argparse
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from src.database import create_database_tables, get_db_session
from src.models import Course, CourseEntitlement, User


def main():
    parser = argparse.ArgumentParser(description="Activate a 99 CNY single-course semester entitlement.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--course-id", required=True, type=int)
    parser.add_argument("--semester-end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--payment-reference", required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    expires = datetime.combine(datetime.strptime(args.semester_end, "%Y-%m-%d").date(), time(23, 59, 59), tzinfo=ZoneInfo("Asia/Shanghai"))
    create_database_tables()
    with get_db_session() as session:
        user = session.scalar(select(User).where(User.email == args.email.strip().lower()))
        course = session.scalar(select(Course).where(Course.id == args.course_id, Course.user_id == (user.id if user else -1)))
        if user is None or course is None:
            raise SystemExit("User or owned course not found.")
        item = CourseEntitlement(user_id=user.id, course_id=course.id, payment_reference=args.payment_reference, expires_at=expires, operator_note=args.note or None)
        session.add(item)
        session.flush()
        print(f"Activated entitlement {item.id} for {user.email} / {course.name} until {expires.isoformat()}")


if __name__ == "__main__":
    main()
