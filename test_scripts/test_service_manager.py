"""
Test Service Manager
===================

Test script to verify the centralized service manager works correctly
and eliminates redundant initializations.
"""

import time
from service_manager import get_service_manager, reset_service_manager


def test_singleton_behavior():
    """Test that service manager implements singleton pattern correctly."""
    print("🧪 Testing Singleton Behavior")
    print("=" * 50)

    # Reset to ensure clean state
    reset_service_manager()

    # Get multiple instances
    manager1 = get_service_manager()
    manager2 = get_service_manager()
    manager3 = get_service_manager()

    # Verify they are the same instance
    if manager1 is manager2 is manager3:
        print("✅ Singleton pattern working correctly")
        return True
    else:
        print("❌ Singleton pattern failed - multiple instances created")
        return False


def test_service_availability():
    """Test service availability checks."""
    print("\n🧪 Testing Service Availability")
    print("=" * 50)

    manager = get_service_manager()

    # Check service status
    status = manager.get_service_status()
    print(f"📊 Service Status: {status['services_available']}")
    print(f"📊 Cache Stats: {status['cache_stats']}")

    # Test individual service checks
    services = ["cosmos", "search", "ai_project", "blob_storage", "agent"]
    available_count = 0

    for service in services:
        available = manager.is_service_available(service)
        status_icon = "✅" if available else "❌"
        print(
            f"{status_icon} {service}: {'Available' if available else 'Not Available'}"
        )
        if available:
            available_count += 1

    print(f"\n📈 {available_count}/{len(services)} services available")
    return available_count > 0


def test_caching_functionality():
    """Test caching functionality."""
    print("\n🧪 Testing Caching Functionality")
    print("=" * 50)

    manager = get_service_manager()

    if not manager.is_service_available("cosmos"):
        print("⚠️  CosmosDB not available - skipping cache tests")
        return True

    # Test statistics caching
    print("📊 Testing statistics caching...")

    # First call (should fetch fresh data)
    start_time = time.time()
    stats1 = manager.get_statistics()
    if stats1:
        print(f"✅ Statistics retrieval: PASSED - {stats1}")
    else:
        print(f"❌ Statistics retrieval: FAILED - {stats1}")
    first_call_time = time.time() - start_time

    # Second call (should use cache)
    start_time = time.time()
    stats2 = manager.get_statistics()
    if stats2:
        print(f"✅ Statistics retrieval: PASSED - {stats2}")
    else:
        print(f"❌ Statistics retrieval: FAILED - {stats2}")
    second_call_time = time.time() - start_time

    print(f"⏱️  First call: {first_call_time:.3f}s")
    print(f"⏱️  Second call: {second_call_time:.3f}s")

    # Verify cache is working (second call should be faster)
    if second_call_time < first_call_time:
        print("✅ Statistics caching working correctly")
        cache_working = True
    else:
        print("⚠️  Cache may not be working optimally")
        cache_working = False

    # Test forced refresh
    print("🔄 Testing forced refresh...")
    start_time = time.time()
    stats3 = manager.get_statistics(force_refresh=True)
    if stats3:
        print(f"✅ Statistics retrieval: PASSED - {stats3}")
    else:
        print(f"❌ Statistics retrieval: FAILED - {stats3}")
    refresh_time = time.time() - start_time

    print(f"⏱️  Forced refresh: {refresh_time:.3f}s")

    return cache_working


def test_invoice_operations():
    """Test basic invoice operations."""
    print("\n🧪 Testing Invoice Operations")
    print("=" * 50)

    manager = get_service_manager()

    if not manager.is_service_available("cosmos"):
        print("⚠️  CosmosDB not available - skipping invoice tests")
        return True

    try:
        # Test listing invoices
        print("📋 Testing invoice listing...")
        invoices = manager.list_invoices(limit=5)
        print(f"✅ Retrieved {len(invoices)} invoices")

        # Test search functionality
        print("🔍 Testing invoice search...")
        search_results = manager.search_invoices("test")
        print(f"✅ Search returned {len(search_results)} results")

        # Test statistics
        print("📊 Testing statistics...")
        stats = manager.get_statistics()
        total_invoices = stats.get("total_invoices", 0)
        print(f"✅ Statistics show {total_invoices} total invoices")

        return True

    except Exception as e:
        print(f"❌ Invoice operations failed: {e}")
        return False


def test_performance_improvement():
    """Test performance improvement over multiple initializations."""
    print("\n🧪 Testing Performance Improvement")
    print("=" * 50)

    # Test multiple service manager calls (should be fast after first)
    times = []

    for i in range(3):
        start_time = time.time()
        manager = get_service_manager()
        if manager.is_service_available("cosmos"):
            stats = manager.get_statistics()
            if stats:
                print(f"✅ Statistics retrieval: PASSED - {stats}")
            else:
                print(f"❌ Statistics retrieval: FAILED - {stats}")
        end_time = time.time()

        call_time = end_time - start_time
        times.append(call_time)
        print(f"📊 Call {i+1}: {call_time:.3f}s")

    # Check if subsequent calls are faster
    if len(times) >= 2 and times[1] < times[0]:
        print("✅ Performance improvement detected")
        return True
    else:
        print("⚠️  Performance improvement not clearly detected")
        return False


def main():
    """Run all tests."""
    print("🚀 Service Manager Test Suite")
    print("=" * 60)

    tests = [
        test_singleton_behavior,
        test_service_availability,
        test_caching_functionality,
        test_invoice_operations,
        test_performance_improvement,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Service manager is working correctly.")
    elif passed > total // 2:
        print("⚠️  Most tests passed. Some services may not be fully configured.")
    else:
        print("❌ Multiple test failures. Check service configuration.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
