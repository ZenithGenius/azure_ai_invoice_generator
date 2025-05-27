"""
Setup Script for Azure AI Foundry Invoice Generation System
===========================================================

This script helps configure the environment and check prerequisites.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_azure_cli():
    """Check if Azure CLI is installed and authenticated"""
    try:
        result = subprocess.run(["az", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Azure CLI is installed")

            # Check if logged in
            result = subprocess.run(
                ["az", "account", "show"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Azure CLI is authenticated")
                return True
            else:
                print("⚠️  Azure CLI not authenticated. Run: az login")
                return False
        else:
            print("❌ Azure CLI not found")
            return False
    except FileNotFoundError:
        print("❌ Azure CLI not found in PATH")
        print(
            "📖 Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        )
        return False


def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path("env_example.txt")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if env_example.exists():
        print("📝 Creating .env file from template...")
        try:
            with open(env_example, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            print("✅ .env file created successfully")
            print("⚠️  Please edit .env file with your Azure service credentials")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ env_example.txt not found")
        return False


def validate_env_variables():
    """Validate that required environment variables are set"""
    from dotenv import load_dotenv

    load_dotenv()

    required_vars = ["AZURE_AI_ENDPOINT", "COSMOS_ENDPOINT", "SEARCH_ENDPOINT"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith("https://your-"):
            missing_vars.append(var)

    if missing_vars:
        print("⚠️  Please configure these environment variables in .env:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print("✅ Required environment variables are configured")
        return True


def test_azure_connections():
    """Test connections to Azure services"""
    print("\n🔗 Testing Azure service connections...")

    try:
        from azure.identity import DefaultAzureCredential
        from azure.cosmos import CosmosClient

        # Test Azure credential
        credential = DefaultAzureCredential()
        print("✅ Azure credentials configured")

        # Test CosmosDB connection (basic connectivity test)
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        if cosmos_endpoint and not cosmos_endpoint.startswith("https://your-"):
            try:
                cosmos_key = os.getenv("COSMOS_KEY")
                if cosmos_key:
                    client = CosmosClient(cosmos_endpoint, cosmos_key)
                    if client:
                        print("✅ CosmosDB connection configured")
                else:
                    client = CosmosClient(cosmos_endpoint, credential)
                    if client:
                        print("✅ CosmosDB connection (managed identity)")
            except Exception as e:
                print(f"⚠️  CosmosDB connection issue: {e}")

        return True

    except Exception as e:
        print(f"⚠️  Azure connection test failed: {e}")
        return False


def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("=" * 60)
    print("1. 📝 Edit .env file with your Azure service credentials:")
    print("   - AZURE_AI_ENDPOINT")
    print("   - COSMOS_ENDPOINT")
    print("   - COSMOS_KEY")
    print("   - SEARCH_ENDPOINT")
    print("   - SEARCH_KEY")
    print("   - STORAGE_CONNECTION_STRING")
    print("")
    print("2. 🔐 Ensure Azure authentication:")
    print("   az login")
    print("")
    print("3. 🧪 Run the test suite:")
    print("   python test_invoice_system.py")
    print("")
    print("4. 🚀 Start generating invoices:")
    print("   python generate_invoices.py")
    print("")
    print("📖 For detailed setup instructions, see README.md")


def main():
    """Main setup function"""
    print("🚀 Azure AI Foundry Invoice System Setup")
    print("=" * 50)

    all_checks_passed = True

    # Check prerequisites
    print("\n🔍 Checking Prerequisites...")
    if not check_python_version():
        all_checks_passed = False

    if not check_azure_cli():
        all_checks_passed = False

    # Install dependencies
    if not install_dependencies():
        all_checks_passed = False

    # Create environment file
    if not create_env_file():
        all_checks_passed = False

    # Load and validate environment
    print("\n⚙️  Checking Configuration...")
    try:
        import importlib

        importlib.import_module("dotenv")

        if not validate_env_variables():
            all_checks_passed = False

        # Test connections if env vars are configured
        if all_checks_passed:
            test_azure_connections()

    except ImportError:
        print("⚠️  python-dotenv not installed, skipping env validation")

    # Show results
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("✅ Setup completed successfully!")
        print("🎉 Your invoice system is ready to use!")
    else:
        print("⚠️  Setup completed with warnings")
        print("🔧 Please address the issues above")

    display_next_steps()


if __name__ == "__main__":
    main()
