from dataclasses import asdict, dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class BillingProduct:
    product_code: str
    name: str
    description: str
    amount_cents: int
    currency: str
    duration_policy: str
    follow_allowance: int
    textbook_allowance: int
    exam_allowance: int
    assistant_allowance: int
    active: bool = True

    def snapshot(self):
        return asdict(self)


_PRODUCTS = MappingProxyType(
    {
        "course_space": BillingProduct(
            product_code="course_space",
            name="Course AI Space",
            description="Course-scoped AI organization, analysis, exam preparation, and assistant access.",
            amount_cents=2990,
            currency="CNY",
            duration_policy="semester_end",
            follow_allowance=30,
            textbook_allowance=10,
            exam_allowance=10,
            assistant_allowance=200,
            active=True,
        ),
    }
)


def get_billing_product(product_code, include_inactive=False):
    product = _PRODUCTS.get(str(product_code).strip())
    if product is None or (not include_inactive and not product.active):
        return None
    return product


def list_billing_products(include_inactive=False):
    return [
        product
        for product in _PRODUCTS.values()
        if include_inactive or product.active
    ]
