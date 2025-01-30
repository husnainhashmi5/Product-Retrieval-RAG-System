from __future__ import annotations

import re
from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any


COLOR_MAP = {
    "black": "Black",
    "blue": "Blue",
    "chocolate": "Chocolate",
    "golden": "Golden",
    "gray": "Grey",
    "green": "Green",
    "grey": "Grey",
    "light gray": "Light Grey",
    "light grey": "Light Grey",
    "purple": "Purple",
    "red": "Red",
    "silver": "Silver",
    "white": "White",
}

KNOWN_BRANDS = {
    "apple": "Apple",
    "candy": "Candy",
    "dell": "Dell",
    "haier": "Haier",
    "hp": "HP",
    "lenovo": "Lenovo",
    "samsung": "Samsung",
    "sony": "Sony",
    "tcl": "TCL",
}

HAIER_MODEL_PREFIXES = (
    "HCC",
    "HCF",
    "HDF",
    "HGL",
    "HMN",
    "HMW",
    "HRF",
    "HSU",
    "HW",
    "HWM",
)


@dataclass(frozen=True)
class ProductRecord:
    product_id: str
    name: str
    brand: str
    model: str
    category: str
    price: int | None
    color: str
    variation: str
    status: str
    source_url: str
    source_row: str
    raw: dict[str, Any] = field(default_factory=dict)

    def searchable_text(self) -> str:
        parts = [
            self.name,
            self.brand,
            self.model,
            self.category,
            self.color,
            self.variation,
            f"Rs {self.price}" if self.price is not None else "",
        ]
        return " | ".join(part for part in parts if part)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "category": self.category,
            "price": self.price,
            "color": self.color,
            "variation": self.variation,
            "status": self.status,
            "source_url": self.source_url,
            "source_row": self.source_row,
        }


@dataclass(frozen=True)
class ValidationReport:
    product_id: str
    row_number: int | None
    is_valid: bool
    reasons: list[str]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_price(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    text = normalize_text(value).lower()
    if not text:
        return None

    text = text.replace("pkr", "").replace("rs.", "").replace("rs", "").replace("rupees", "")
    text = text.replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)(k)?", text)
    if not match:
        return None

    number = float(match.group(1))
    if match.group(2):
        number *= 1000
    return int(number)


def normalize_status(value: Any) -> str:
    text = normalize_text(value).lower()
    if text in {"active", "available", "in stock", "enabled"}:
        return "active"
    if text in {"inactive", "disabled", "out of stock", "discontinued"}:
        return "inactive"
    return "unknown"


def normalize_model(value: Any) -> str:
    text = normalize_text(value)
    if not text or text.lower() == "missing":
        return ""
    text = re.sub(r"\s*-\s*", "-", text)
    if "-" in text or "/" in text:
        return re.sub(r"\s+", " ", text).upper()

    if not re.search(r"\s", text):
        return text.upper()

    tokens = re.findall(r"[A-Za-z]+|\d+", text)
    if len(tokens) > 1:
        return "-".join(token.upper() for token in tokens)
    return text.upper()


def normalize_category(value: Any) -> str:
    text = normalize_text(value).lower()
    if not text:
        return ""

    checks = [
        ("washing machine", ("washing", "washer")),
        ("refrigerator", ("refrigerator", "fridge", "cooling")),
        ("microwave", ("microwave", "oven")),
        ("television", ("television", "tv", "led", "qled", "oled", "lcd")),
        ("phone", ("phone", "mobile", "smartphone")),
        ("laptop", ("laptop", "notebook")),
        ("hob", ("hob", "burner")),
        ("freezer", ("freezer",)),
        ("air conditioner", ("air conditioner", "ac", "inverter ac")),
    ]
    for normalized, keywords in checks:
        if any(_contains_category_keyword(text, keyword) for keyword in keywords):
            return normalized
    return text.split("/")[-1].strip() or text


def _contains_category_keyword(text: str, keyword: str) -> bool:
    if len(keyword) <= 3:
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text


def build_product_id(name: str, model: str, variation: str, price: int | None) -> str:
    raw = "-".join(
        part
        for part in [
            normalize_text(name),
            normalize_model(model),
            normalize_text(variation),
            str(price or ""),
        ]
        if part
    )
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    if slug:
        return slug
    return f"product-{sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def extract_brand(name: str, model: str) -> str:
    text = f"{name} {model}".lower()
    for keyword, brand in KNOWN_BRANDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            return brand

    normalized_model = normalize_model(model)
    if normalized_model.startswith(HAIER_MODEL_PREFIXES):
        return "Haier"
    return ""


def normalize_color(value: Any, fallback_text: str = "") -> str:
    text = normalize_text(value).lower()
    combined = f"{text} {fallback_text.lower()}"
    for raw, normalized in sorted(COLOR_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(raw)}\b", combined):
            return normalized
    return ""


def normalize_product_row(row: dict[str, Any], row_number: int | None = None) -> ProductRecord:
    name = normalize_text(row.get("Product Info") or row.get("name"))
    variation = normalize_text(row.get("Variation") or row.get("variation"))
    raw_model = row.get("Custom Id") or row.get("custom_id") or row.get("model") or variation
    model = normalize_model(raw_model)
    price = parse_price(row.get("Price(Rs)") or row.get("price"))
    category = normalize_category(row.get("Categories") or row.get("category"))
    status = normalize_status(row.get("Status") or row.get("status"))
    brand = extract_brand(name, model)
    color = normalize_color(variation, name)
    source_url = normalize_text(row.get("source_url") or row.get("Source URL") or row.get("url"))
    product_number = normalize_text(row.get("Product Number") or row.get("source_row"))
    source_row = product_number or (str(row_number) if row_number is not None else "")

    return ProductRecord(
        product_id=build_product_id(name=name, model=model, variation=variation, price=price),
        name=name,
        brand=brand,
        model=model,
        category=category,
        price=price,
        color=color,
        variation=variation,
        status=status,
        source_url=source_url,
        source_row=source_row,
        raw=dict(row),
    )


def validate_product(product: ProductRecord, *, active_only: bool = True, row_number: int | None = None) -> ValidationReport:
    reasons: list[str] = []
    if not product.name:
        reasons.append("missing_name")
    if product.price is None:
        reasons.append("missing_or_invalid_price")
    if product.status == "unknown":
        reasons.append("unknown_status")
    if active_only and product.status != "active":
        reasons.append("status_not_active")

    return ValidationReport(
        product_id=product.product_id,
        row_number=row_number,
        is_valid=not reasons,
        reasons=reasons,
    )
