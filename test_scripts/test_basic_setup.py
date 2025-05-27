"""
Basic Setup Test for Invoice Generation System
==============================================

This script tests basic functionality without requiring full Azure setup.
"""

from pathlib import Path


def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing module imports...")

    try:
        print("✅ config module imported")
    except Exception as e:
        print(f"❌ config module failed: {e}")
        return False

    try:
        print("✅ invoice_instructions module imported")
    except Exception as e:
        print(f"❌ invoice_instructions module failed: {e}")
        return False

    try:
        print("✅ cosmos_service module imported")
    except Exception as e:
        print(f"❌ cosmos_service module failed: {e}")
        return False

    try:
        print("✅ azure_search_service module imported")
    except Exception as e:
        print(f"❌ azure_search_service module failed: {e}")
        return False

    return True


def test_invoice_instructions():
    """Test invoice instructions generation"""
    print("\n📋 Testing invoice instructions...")

    try:
        from invoice_instructions import get_invoice_instructions

        instructions = get_invoice_instructions()

        if len(instructions) > 1000:
            print("✅ Invoice instructions generated successfully")
            print(f"   Length: {len(instructions)} characters")
            return True
        else:
            print("❌ Invoice instructions too short")
            return False

    except Exception as e:
        print(f"❌ Invoice instructions test failed: {e}")
        return False


def test_config_loading():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")

    try:
        import config

        # Check if basic config values exist
        required_configs = [
            "COMPANY_NAME",
            "COMPANY_ADDRESS",
            "COMPANY_PHONE",
            "COMPANY_EMAIL",
        ]

        all_present = True
        for conf in required_configs:
            if hasattr(config, conf):
                print(f"✅ {conf}: {getattr(config, conf)}")
            else:
                print(f"❌ {conf}: Missing")
                all_present = False

        return all_present

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")

    required_files = [
        "requirements.txt",
        "config.py",
        "generate_invoices.py",
        "cosmos_service.py",
        "azure_search_service.py",
        "invoice_instructions.py",
        "env_example.txt",
        "README.md",
    ]

    all_present = True
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - Missing")
            all_present = False

    return all_present


def test_environment_setup():
    """Test environment setup"""
    print("\n🌍 Testing environment setup...")

    env_file = Path(".env")
    env_example = Path("env_example.txt")

    if env_file.exists():
        print("✅ .env file exists")

        # Try to load environment variables
        try:
            from dotenv import load_dotenv

            load_dotenv()
            print("✅ Environment variables loaded")
            return True
        except ImportError:
            print("⚠️  python-dotenv not installed")
            return False
        except Exception as e:
            print(f"⚠️  Environment loading issue: {e}")
            return False

    elif env_example.exists():
        print("⚠️  .env file missing, but env_example.txt exists")
        print("💡 Run: cp env_example.txt .env")
        return False
    else:
        print("❌ No environment files found")
        return False


def test_azure_packages():
    """Test if Azure packages are installed"""
    print("\n☁️  Testing Azure packages...")

    required_packages = [
        "azure.ai.projects",
        "azure.identity",
        "azure.cosmos",
        "azure.search.documents",
        "azure.storage.blob",
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Not installed")
            all_installed = False

    return all_installed


def generate_sample_invoice_data():
    """Generate sample invoice data for testing"""
    print("\n📄 Testing invoice data generation...")

    try:
        from datetime import datetime, timedelta

        sample_data = {
            "invoice_number": "INV-2024-TEST-001",
            "invoice_date": datetime.now().strftime("%m/%d/%Y"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y"),
            "client": {
                "name": "Test Client Corporation",
                "address": "123 Test Street, Test City, TC 12345",
            },
            "line_items": [
                {
                    "description": "Sample Service",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "total": 100.00,
                }
            ],
            "subtotal": 100.00,
            "tax_rate": 0.08,
            "tax_amount": 8.00,
            "total": 108.00,
        }

        print("✅ Sample invoice data generated")
        print(f"   Invoice Number: {sample_data['invoice_number']}")
        print(f"   Client: {sample_data['client']['name']}")
        print(f"   Total: ${sample_data['total']:.2f}")

        return True, sample_data

    except Exception as e:
        print(f"❌ Sample data generation failed: {e}")
        return False, None


def run_basic_tests():
    """Run all basic tests"""
    print("🚀 Running Basic Setup Tests")
    print("=" * 50)

    tests = [
        ("File Structure", test_file_structure),
        ("Environment Setup", test_environment_setup),
        ("Azure Packages", test_azure_packages),
        ("Module Imports", test_imports),
        ("Configuration", test_config_loading),
        ("Invoice Instructions", test_invoice_instructions),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Generate sample data
    print(f"\n🔍 Sample Data Generation...")
    sample_success, sample_data = generate_sample_invoice_data()
    results.append(("Sample Data Generation", sample_success))

    # Print summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if success:
            passed += 1

    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")

    if passed == total:
        print("🎉 All basic tests passed!")
        print("🔄 Next: Run setup_environment.py for full setup")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("🔧 Try running: pip install -r requirements.txt")

    return passed == total


if __name__ == "__main__":
    success = run_basic_tests()

    if success:
        print("\n✅ Basic setup is working correctly!")
        print("🎯 Next steps:")
        print("   1. Run: python setup_environment.py")
        print("   2. Configure your .env file with Azure credentials")
        print("   3. Run: python test_invoice_system.py")
    else:
        print("\n❌ Please resolve the basic setup issues first.")
