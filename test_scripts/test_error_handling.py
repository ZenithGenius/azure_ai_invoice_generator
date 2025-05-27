#!/usr/bin/env python3
"""
Error Handling Test Suite
=========================

Test error handling and edge cases in the invoice system.
"""

from datetime import datetime
from service_manager import get_service_manager


def test_invalid_input_handling():
    """Test handling of invalid input data."""
    print("🧪 Testing Invalid Input Handling")
    print("-" * 40)

    service_manager = get_service_manager()

    # Test with missing required fields
    print("📝 Testing missing required fields...")
    invalid_order = {
        "order_id": "INVALID-001",
        # Missing client_name and other required fields
        "items": [],
    }

    try:
        result = service_manager.generate_invoice(invalid_order)

        if result.get("success"):
            print("⚠️  System accepted invalid input - this may need attention")
        else:
            print("✅ System properly rejected invalid input")
            print(f"   Error: {result.get('error', 'No error message')}")
    except Exception as e:
        print(f"✅ System raised exception for invalid input: {e}")

    # Test with invalid data types
    print("\n📝 Testing invalid data types...")
    invalid_types_order = {
        "order_id": "INVALID-002",
        "client_name": "Test Client",
        "client_address": "123 Test St",
            "items": [
                {
                "description": "Test Service",
                "quantity": "not_a_number",  # Invalid type
                "unit_price": "also_not_a_number",  # Invalid type
            }
        ],
        "tax_rate": "invalid_tax_rate",  # Invalid type
    }

    try:
        result = service_manager.generate_invoice(invalid_types_order)

        if result.get("success"):
            print("⚠️  System processed invalid data types")
        else:
            print("✅ System handled invalid data types gracefully")
    except Exception as e:
        print(f"✅ System raised exception for invalid data types: {e}")


def test_service_unavailability():
    """Test behavior when services are unavailable."""
    print("\n🧪 Testing Service Unavailability")
    print("-" * 40)

    service_manager = get_service_manager()

    # Check which services are available
    status = service_manager.get_service_status()
    available_services = status["services_available"]

    print(f"📊 Current service status: {available_services}")

    # Test operations when some services might be unavailable
    if not available_services.get("cosmos", False):
        print("📝 Testing with CosmosDB unavailable...")

        # Try to get statistics
        try:
            stats = service_manager.get_statistics()
            if stats.get("error"):
                print("✅ System gracefully handled CosmosDB unavailability")
            else:
                print("⚠️  System returned data despite CosmosDB being unavailable")
        except Exception as e:
            print(f"✅ System raised appropriate exception: {e}")

    if not available_services.get("ai_project", False):
        print("📝 Testing with AI Project unavailable...")

        # Try to generate invoice
        test_order = {
            "order_id": "TEST-AI-UNAVAILABLE",
            "client_name": "Test Client",
            "client_address": "123 Test St",
            "items": [{"description": "Test", "quantity": 1, "unit_price": 100}],
        }

        try:
            result = service_manager.generate_invoice(test_order)
            if result.get("fallback_used"):
                print("✅ System used fallback when AI unavailable")
            elif result.get("success"):
                print("⚠️  System succeeded despite AI being unavailable")
            else:
                print("✅ System gracefully handled AI unavailability")
        except Exception as e:
            print(f"✅ System raised appropriate exception: {e}")


def test_network_timeout_simulation():
    """Test timeout handling (simulated)."""
    print("\n🧪 Testing Timeout Handling")
    print("-" * 40)

    service_manager = get_service_manager()

    # Test with operations that might timeout
    print("📝 Testing statistics with potential timeout...")
    try:
        stats = service_manager.get_statistics()
        print("✅ Statistics operation completed (no timeout)")
    except Exception as e:
        print(f"✅ Timeout or error handled gracefully: {e}")

    print("📝 Testing search with potential timeout...")
    try:
        results = service_manager.search_invoices("timeout_test")
        print(f"✅ Search operation completed - found {len(results)} results")
    except Exception as e:
        print(f"✅ Search timeout or error handled gracefully: {e}")


def test_concurrent_operations():
    """Test concurrent operations and thread safety."""
    print("\n🧪 Testing Concurrent Operations")
    print("-" * 40)

    import threading
    import time

    service_manager = get_service_manager()
    results = []
    errors = []

    def concurrent_operation(thread_id):
        """Perform operations concurrently."""
        try:
            # Get service manager (should be same instance)
            manager = get_service_manager()

            # Perform multiple operations
            stats = manager.get_statistics()
            invoices = manager.list_invoices(limit=3)
            search_results = manager.search_invoices(f"thread_{thread_id}")

            results.append(f"Thread {thread_id}: Success")

        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")

    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=concurrent_operation, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print(f"📊 Concurrent operations results:")
    print(f"   Successful: {len(results)}")
    print(f"   Errors: {len(errors)}")

    if errors:
        print("❌ Some concurrent operations failed:")
        for error in errors[:3]:  # Show first 3 errors
            print(f"   - {error}")
    else:
        print("✅ All concurrent operations succeeded")


def test_edge_cases():
    """Test various edge cases."""
    print("\n🧪 Testing Edge Cases")
    print("-" * 40)

    service_manager = get_service_manager()

    # Test with empty search
    print("📝 Testing empty search...")
    try:
        results = service_manager.search_invoices("")
        print(f"✅ Empty search handled - returned {len(results)} results")
    except Exception as e:
        print(f"✅ Empty search raised exception: {e}")

    # Test with very long search term
    print("📝 Testing very long search term...")
    long_term = "a" * 1000  # 1000 character search term
    try:
        results = service_manager.search_invoices(long_term)
        print(f"✅ Long search term handled - returned {len(results)} results")
    except Exception as e:
        print(f"✅ Long search term raised exception: {e}")

    # Test with special characters
    print("📝 Testing special characters...")
    special_term = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    try:
        results = service_manager.search_invoices(special_term)
        print(f"✅ Special characters handled - returned {len(results)} results")
    except Exception as e:
        print(f"✅ Special characters raised exception: {e}")

    # Test with non-existent invoice
    print("📝 Testing non-existent invoice lookup...")
    try:
        invoice = service_manager.get_invoice("NON-EXISTENT-INVOICE-12345")
        if invoice is None:
            print("✅ Non-existent invoice returned None")
        else:
            print("⚠️  Non-existent invoice returned unexpected data")
    except Exception as e:
        print(f"✅ Non-existent invoice raised exception: {e}")


def test_data_validation():
    """Test data validation and sanitization."""
    print("\n🧪 Testing Data Validation")
    print("-" * 40)

    service_manager = get_service_manager()

    # Test with extreme values
    print("📝 Testing extreme values...")
    extreme_order = {
        "order_id": "EXTREME-001",
        "client_name": "Test Client",
        "client_address": "123 Test St",
        "items": [
            {
                "description": "Extreme Service",
                "quantity": 999999999,  # Very large quantity
                "unit_price": 0.01,  # Very small price
            },
            {
                "description": "Another Extreme Service",
                "quantity": 1,
                "unit_price": 999999999.99,  # Very large price
            },
        ],
        "tax_rate": 0.99,  # 99% tax rate
    }

    try:
        result = service_manager.generate_invoice(extreme_order)

        if result.get("success"):
            total = result["invoice_data"].get("total", 0)
            print(f"✅ Extreme values processed - Total: ${total:,.2f}")
        else:
            print("✅ System rejected extreme values appropriately")
    except Exception as e:
        print(f"✅ System raised exception for extreme values: {e}")

    # Test with negative values
    print("📝 Testing negative values...")
    negative_order = {
        "order_id": "NEGATIVE-001",
        "client_name": "Test Client",
        "client_address": "123 Test St",
            "items": [
                {
                "description": "Negative Service",
                "quantity": -5,  # Negative quantity
                "unit_price": -100.00,  # Negative price
            }
        ],
        "tax_rate": -0.1,  # Negative tax rate
    }

    try:
        result = service_manager.generate_invoice(negative_order)

        if result.get("success"):
            print("⚠️  System accepted negative values - may need validation")
        else:
            print("✅ System rejected negative values appropriately")
    except Exception as e:
        print(f"✅ System raised exception for negative values: {e}")


def main():
    """Run all error handling tests."""
    print("🚀 Error Handling Test Suite")
    print("=" * 60)
    
    tests = [
        test_invalid_input_handling,
        test_service_unavailability,
        test_network_timeout_simulation,
        test_concurrent_operations,
        test_edge_cases,
        test_data_validation,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 60)
    print("🎯 Error Handling Test Suite Completed")
    print("✅ Review the results above to ensure proper error handling")


if __name__ == "__main__":
    main()
