#!/usr/bin/env python3
"""
Debug test to isolate the JSON parsing issue
"""

import json
import re
from datetime import datetime


def test_json_parsing():
    """Test JSON parsing with sample data."""

    # Test the JSON structure from invoice instructions
    sample_json = """
    {
        "invoice_number": "INV-YYYY-NNNNNN",
        "invoice_date": "MM/DD/YYYY",
        "due_date": "MM/DD/YYYY",
        "client": {
            "name": "Client Name",
            "address": "Full Address",
            "contact": "Contact Info"
        },
        "line_items": [
            {
                "description": "Service/Product Description",
                "quantity": 1,
                "unit_price": 100.00,
                "total": 100.00
            }
        ],
        "subtotal": 100.00,
        "tax_rate": 0.08,
        "tax_amount": 8.00,
        "total": 108.00
    }
    """

    try:
        print("Testing JSON parsing...")
        data = json.loads(sample_json)
        print("✅ JSON parsed successfully")
        print(f"Invoice number: {data.get('invoice_number')}")
        return True
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        return False


def test_extract_field():
    """Test the field extraction logic."""

    def _extract_field(text: str, *field_names) -> str:
        """Extract a field value from text using multiple possible field names."""
        for field_name in field_names:
            pattern = rf"{field_name}[:\s]+([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    sample_text = """
    Invoice Number: INV-2024-000001
    Client Name: Test Client
    Total Amount: $1,000.00
    """

    try:
        print("\nTesting field extraction...")
        invoice_num = _extract_field(sample_text, "invoice.number", "Invoice Number")
        print(f"✅ Extracted invoice number: '{invoice_num}'")

        client = _extract_field(sample_text, "client", "Client Name")
        print(f"✅ Extracted client: '{client}'")

        return True
    except Exception as e:
        print(f"❌ Field extraction failed: {e}")
        return False


def test_generate_invoice_number():
    """Test invoice number generation."""
    try:
        print("\nTesting invoice number generation...")
        now = datetime.now()
        invoice_number = f"INV-{now.year}-{now.month:02d}{now.day:02d}-{now.hour:02d}{now.minute:02d}{now.second:02d}"
        print(f"✅ Generated invoice number: {invoice_number}")
        return True
    except Exception as e:
        print(f"❌ Invoice number generation failed: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Debug Test - Isolating JSON Parsing Issue")
    print("=" * 50)

    test1 = test_json_parsing()
    test2 = test_extract_field()
    test3 = test_generate_invoice_number()

    print("\n" + "=" * 50)
    if all([test1, test2, test3]):
        print("✅ All debug tests passed!")
    else:
        print("❌ Some debug tests failed!")
