from app.ingestion.normalizer import (
    build_product_id,
    normalize_category,
    normalize_model,
    normalize_product_row,
    normalize_status,
    parse_price,
    validate_product,
)


def test_parse_price_handles_common_rupee_formats():
    assert parse_price("Rs 50,000") == 50000
    assert parse_price("49,999") == 49999
    assert parse_price("50k") == 50000
    assert parse_price("") is None
    assert parse_price("missing") is None


def test_normalize_status_does_not_treat_blank_as_active():
    assert normalize_status("active") == "active"
    assert normalize_status("Inactive") == "inactive"
    assert normalize_status("") == "unknown"
    assert normalize_status(None) == "unknown"


def test_normalize_model_and_category_are_stable():
    assert normalize_model(" HRF-622ICG ") == "HRF-622ICG"
    assert normalize_model("hrf 622 icg") == "HRF-622-ICG"
    assert normalize_category("Home Appliances/Washing Machines/Top Load Fully Automatic") == "washing machine"
    assert normalize_category("Home Appliances/Televisions/QLED Series") == "television"


def test_build_product_id_is_stable_from_model_and_name():
    product_id = build_product_id(
        name="Samsung Galaxy A16",
        model="A16",
        variation="Black",
        price=48999,
    )

    assert product_id == "samsung-galaxy-a16-a16-black-48999"


def test_validate_product_rejects_blank_status_when_active_only():
    product = normalize_product_row(
        {
            "Price(Rs)": "48999",
            "Product Info": "Samsung Galaxy A16",
            "Variation": "Black",
            "Custom Id": "A16",
            "Product Number": "row-1",
            "Status": "",
            "Categories": "Mobiles/Phones",
        }
    )

    report = validate_product(product, active_only=True)

    assert report.is_valid is False
    assert "status_not_active" in report.reasons
    assert product.status == "unknown"


def test_normalize_product_row_extracts_brand_color_and_metadata():
    product = normalize_product_row(
        {
            "Price(Rs)": "216,999",
            "Product Info": "HW100-BP14929S3 - 10 kg Fully Automatic Front Load Washing Machine",
            "Variation": "Grey",
            "Custom Id": "HW100-BP14929S3",
            "Product Number": "20240127111925845",
            "Status": "active",
            "Categories": "Home Appliances/Washing Machines/Front Load Fully Automatic",
        }
    )

    assert product.price == 216999
    assert product.brand == "Haier"
    assert product.model == "HW100-BP14929S3"
    assert product.category == "washing machine"
    assert product.color == "Grey"
    assert product.status == "active"
