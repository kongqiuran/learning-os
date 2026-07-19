import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.dependencies import require_current_user
from src.api.factory import create_app
from src.billing.product_catalog import get_billing_product, list_billing_products
from src.database import create_database_tables, get_db_session
from src.models import CourseEntitlement, PaymentOrder, User
from src.services.course_service import create_course
from src.services.payment_order_service import (
    BillingProductInactiveError,
    BillingProductNotFoundError,
    PaymentOrderCourseNotFoundError,
    PaymentOrderStateError,
    activate_payment_order,
    create_payment_order,
    get_payment_order_for_user,
)
from src.services.user_service import register_user


NOW = datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)


class PaymentOrderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            session.query(User).delete()
        self.user = register_user(f"buyer-{id(self)}@example.com", "password")
        self.other_user = register_user(f"other-{id(self)}@example.com", "password")
        self.course = create_course(self.user.id, "Signals")
        self.other_course = create_course(self.other_user.id, "Private Course")

    def test_catalog_exposes_active_course_space_product(self):
        product = get_billing_product("course_space")
        self.assertIsNotNone(product)
        self.assertEqual(product.amount_cents, 2990)
        self.assertEqual(product.follow_allowance, 30)
        self.assertEqual([item.product_code for item in list_billing_products()], ["course_space"])

    def test_inactive_product_cannot_be_purchased(self):
        inactive = replace(get_billing_product("course_space"), active=False)
        with patch("src.services.payment_order_service.get_billing_product", return_value=inactive):
            with self.assertRaises(BillingProductInactiveError):
                create_payment_order(self.user.id, self.course.id, "course_space", "inactive-request")

    def test_unknown_product_cannot_be_purchased(self):
        with self.assertRaises(BillingProductNotFoundError):
            create_payment_order(self.user.id, self.course.id, "missing-product", "missing-product-request")

    def test_creates_order_from_catalog_snapshot(self):
        order = create_payment_order(self.user.id, self.course.id, "course_space", "request-one")
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.amount_cents, 2990)
        self.assertEqual(order.currency, "CNY")
        self.assertEqual(order.product_snapshot["assistant_allowance"], 200)
        self.assertTrue(order.order_no.startswith("LO-"))

    def test_repeated_request_key_returns_original_order(self):
        first = create_payment_order(self.user.id, self.course.id, "course_space", "same-request")
        second = create_payment_order(self.user.id, self.course.id, "course_space", "same-request")
        self.assertEqual(first.id, second.id)
        with get_db_session() as session:
            self.assertEqual(session.query(PaymentOrder).filter_by(user_id=self.user.id).count(), 1)

    def test_user_cannot_purchase_another_users_course(self):
        with self.assertRaises(PaymentOrderCourseNotFoundError):
            create_payment_order(self.user.id, self.other_course.id, "course_space", "forbidden-request")

    def test_activation_creates_catalog_entitlement_and_marks_order_paid(self):
        order = create_payment_order(self.user.id, self.course.id, "course_space", "activation-request")
        entitlement = activate_payment_order(order.order_no, operator_note="manual payment confirmed", now=NOW)
        self.assertEqual(entitlement.product_code, "course_space")
        self.assertEqual(entitlement.amount_cents, 2990)
        self.assertEqual(entitlement.follow_remaining, 30)
        self.assertEqual(entitlement.textbook_remaining, 10)
        self.assertEqual(entitlement.exam_remaining, 10)
        self.assertEqual(entitlement.assistant_remaining, 200)
        with get_db_session() as session:
            stored = session.get(PaymentOrder, order.id)
            self.assertEqual(stored.status, "paid")
            self.assertEqual(stored.entitlement_id, entitlement.id)
            self.assertEqual(stored.operator_note, "manual payment confirmed")

    def test_repeated_activation_returns_same_entitlement(self):
        order = create_payment_order(self.user.id, self.course.id, "course_space", "repeat-activation")
        first = activate_payment_order(order.order_no, now=NOW)
        second = activate_payment_order(order.order_no, now=NOW)
        self.assertEqual(first.id, second.id)
        with get_db_session() as session:
            self.assertEqual(session.query(CourseEntitlement).filter_by(course_id=self.course.id).count(), 1)

    def test_concurrent_activation_creates_one_entitlement(self):
        order = create_payment_order(self.user.id, self.course.id, "course_space", "concurrent-activation")
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _index: activate_payment_order(order.order_no, now=NOW), range(2)))
        self.assertEqual(results[0].id, results[1].id)
        with get_db_session() as session:
            self.assertEqual(session.query(CourseEntitlement).filter_by(course_id=self.course.id).count(), 1)

    def test_cancelled_order_cannot_be_activated(self):
        order = create_payment_order(self.user.id, self.course.id, "course_space", "cancelled-order")
        with get_db_session() as session:
            session.get(PaymentOrder, order.id).status = "cancelled"
        with self.assertRaises(PaymentOrderStateError):
            activate_payment_order(order.order_no, now=NOW)


class PaymentOrderApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        with get_db_session() as session:
            session.query(User).delete()
        self.user = register_user(f"api-buyer-{id(self)}@example.com", "password")
        self.other_user = register_user(f"api-other-{id(self)}@example.com", "password")
        self.course = create_course(self.user.id, "Control Systems")
        self.app = create_app(session_secret="payment-order-test-secret")
        self.app.dependency_overrides[require_current_user] = lambda: self.user
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()

    def test_products_and_order_endpoints(self):
        products = self.client.get("/api/billing/products")
        self.assertEqual(products.status_code, 200)
        self.assertEqual(products.json()["products"][0]["product_code"], "course_space")
        self.assertEqual(products.json()["products"][0]["amount_cents"], 2990)

        created = self.client.post(
            "/api/billing/orders",
            json={"course_id": self.course.id, "product_code": "course_space", "request_key": "api-request"},
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["status"], "pending")

        fetched = self.client.get(f"/api/billing/orders/{created.json()['order_no']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["course_id"], self.course.id)

    def test_user_cannot_query_another_users_order(self):
        order = create_payment_order(self.other_user.id, create_course(self.other_user.id, "Other").id, "course_space", "other-order")
        response = self.client.get(f"/api/billing/orders/{order.order_no}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "payment_order_not_found")


if __name__ == "__main__":
    unittest.main()
