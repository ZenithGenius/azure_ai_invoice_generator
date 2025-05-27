"""
CosmosDB Service for Invoice Management
======================================

This module handles all CosmosDB operations for storing and retrieving invoices.
"""

from datetime import datetime, UTC
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from typing import Dict, List, Optional
import config


class CosmosDBService:
    """Service class for managing invoices in CosmosDB."""

    def __init__(self):
        """Initialize the CosmosDB service."""
        self.client = None
        self.database = None
        self.container = None

        print("🔄 Initializing CosmosDB service...")

        # Validate configuration
        if not self._validate_config():
            return

        # Initialize client
        if not self._initialize_client():
            return

        # Initialize database and container
        if not self._initialize_database_and_container():
            return

        print("✅ CosmosDB service initialized successfully")

    def _validate_config(self) -> bool:
        """Validate CosmosDB configuration."""
        print("🔍 Validating CosmosDB configuration...")

        if not config.COSMOS_ENDPOINT:
            print("❌ COSMOS_ENDPOINT not configured")
            return False

        if not config.COSMOS_KEY:
            print("❌ COSMOS_KEY not configured")
            return False

        print(f"✅ Endpoint: {config.COSMOS_ENDPOINT}")
        print(f"✅ Database: {config.COSMOS_DATABASE_NAME}")
        print(f"✅ Container: {config.COSMOS_CONTAINER_NAME}")
        return True

    def _initialize_client(self) -> bool:
        """Initialize the CosmosDB client with proper error handling."""
        try:
            print("🔄 Creating CosmosDB client...")

            # Use key-based authentication for better reliability
            self.client = CosmosClient(
                url=config.COSMOS_ENDPOINT,
                credential=config.COSMOS_KEY,
                consistency_level="Session",
            )

            # Test the connection
            print("🔄 Testing CosmosDB connection...")
            database_iterator = self.client.list_databases()
            list(database_iterator)  # Force evaluation to test connection

            print("✅ CosmosDB client created and connection tested")
            return True

        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ CosmosDB HTTP error: {e.status_code} - {e.message}")
            if e.status_code == 401:
                print("   ⚠️  Authentication failed - check your COSMOS_KEY")
            elif e.status_code == 403:
                print("   ⚠️  Access forbidden - check permissions")
            elif e.status_code == 404:
                print("   ⚠️  Resource not found - check COSMOS_ENDPOINT")
            return False

        except Exception as e:
            print(f"❌ Error creating CosmosDB client: {e}")
            print(f"   Error type: {type(e).__name__}")
            return False

    def _initialize_database_and_container(self) -> bool:
        """Initialize database and container."""
        try:
            print("🔄 Creating/getting database...")

            # Create or get database
            self.database = self.client.create_database_if_not_exists(
                id=config.COSMOS_DATABASE_NAME
            )
            print(f"✅ Database '{config.COSMOS_DATABASE_NAME}' ready")

            print("🔄 Creating/getting container...")

            # Create or get container
            self.container = self.database.create_container_if_not_exists(
                id=config.COSMOS_CONTAINER_NAME,
                partition_key=PartitionKey(path="/invoice_number"),
                offer_throughput=400,
            )
            print(f"✅ Container '{config.COSMOS_CONTAINER_NAME}' ready")

            # Test container access
            print("🔄 Testing container access...")
            self.container.read()
            print("✅ Container access confirmed")

            return True

        except exceptions.CosmosResourceExistsError:
            print("✅ Database/Container already exists")
            return True

        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ CosmosDB HTTP error during setup: {e.status_code} - {e.message}")
            return False

        except Exception as e:
            print(f"❌ Error setting up database/container: {e}")
            return False

    def is_available(self) -> bool:
        """Check if CosmosDB service is available."""
        return self.container is not None

    def save_invoice(self, invoice_data: Dict) -> bool:
        """
        Save invoice data to CosmosDB.

        Args:
            invoice_data (Dict): Invoice data to save

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            print("❌ CosmosDB not available - cannot save invoice")
            return False

        try:
            print(
                f"🔄 Saving invoice {invoice_data.get('invoice_number', 'Unknown')} to CosmosDB..."
            )

            # Add metadata
            invoice_item = {
                "id": invoice_data.get("invoice_number"),
                "invoice_number": invoice_data.get("invoice_number"),
                "created_date": datetime.now(UTC).isoformat(),
                "status": "active",
                "invoice_data": invoice_data,
            }

            # Insert into CosmosDB
            response = self.container.create_item(body=invoice_item)
            print(f"✅ Invoice {invoice_data.get('invoice_number')} saved successfully")
            print(f"   Resource ID: {response.get('id')}")
            return True

        except exceptions.CosmosResourceExistsError:
            print(f"⚠️  Invoice {invoice_data.get('invoice_number')} already exists")
            return False

        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ HTTP error saving invoice: {e.status_code} - {e.message}")
            return False

        except Exception as e:
            print(f"❌ Error saving invoice to CosmosDB: {e}")
            return False

    def get_invoice(self, invoice_number: str) -> Optional[Dict]:
        """
        Retrieve invoice by invoice number.

        Args:
            invoice_number (str): Invoice number to retrieve

        Returns:
            Optional[Dict]: Invoice data if found, None otherwise
        """
        if not self.is_available():
            print("❌ CosmosDB not available - cannot retrieve invoice")
            return None

        try:
            print(f"🔄 Retrieving invoice {invoice_number}...")
            item = self.container.read_item(
                item=invoice_number, partition_key=invoice_number
            )
            print(f"✅ Invoice {invoice_number} retrieved successfully")
            return item

        except exceptions.CosmosResourceNotFoundError:
            print(f"⚠️  Invoice {invoice_number} not found")
            return None

        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ HTTP error retrieving invoice: {e.status_code} - {e.message}")
            return None

        except Exception as e:
            print(f"❌ Error retrieving invoice: {e}")
            return None

    def list_invoices(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        List invoices with optimized query and pagination.

        Args:
            limit (int): Maximum number of invoices to return
            offset (int): Number of invoices to skip (for pagination)

        Returns:
            List[Dict]: List of invoice documents
        """
        if not self.is_available():
            return []

        try:
            print(f"🔄 Listing up to {limit} invoices (offset: {offset})...")

            # Optimized query with specific field selection for better performance
            query = """
                SELECT c.id, c.invoice_number, c.invoice_date, c.due_date, 
                       c.client, c.total, c.status, c.currency, c._ts
                FROM c 
                WHERE c.invoice_number != null
                ORDER BY c._ts DESC
                OFFSET @offset LIMIT @limit
            """

            parameters = [
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit},
            ]

            # Execute query with optimized settings
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=limit,  # Optimize page size
                )
            )

            print(f"✅ Retrieved {len(items)} invoices")
            return items

        except Exception as e:
            print(f"Error listing invoices: {e}")
            return []

    def search_invoices(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search invoices with optimized full-text search.

        Args:
            search_term (str): Search term to look for
            limit (int): Maximum number of results

        Returns:
            List[Dict]: List of matching invoice documents
        """
        if not self.is_available():
            return []

        try:
            print(f"🔍 Searching for: '{search_term}'...")

            # Optimized search query with multiple field matching
            search_term_lower = search_term.lower()

            query = """
                SELECT c.id, c.invoice_number, c.invoice_date, c.client, 
                       c.total, c.status, c.line_items, c._ts
                FROM c 
                WHERE (
                    CONTAINS(LOWER(c.invoice_number), @search_term) OR
                    CONTAINS(LOWER(c.client.name), @search_term) OR
                    CONTAINS(LOWER(c.client.address), @search_term) OR
                    CONTAINS(LOWER(c.client.contact), @search_term) OR
                    EXISTS(
                        SELECT VALUE item 
                        FROM item IN c.line_items 
                        WHERE CONTAINS(LOWER(item.description), @search_term)
                    )
                )
                ORDER BY c._ts DESC
                OFFSET 0 LIMIT @limit
            """

            parameters = [
                {"name": "@search_term", "value": search_term_lower},
                {"name": "@limit", "value": limit},
            ]

            # Execute optimized search
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=limit,
                )
            )

            print(f"✅ Found {len(items)} matching invoices")
            return items

        except Exception as e:
            print(f"Error searching invoices: {e}")
            return []

    def update_invoice_status(self, invoice_number: str, status: str) -> bool:
        """
        Update invoice status.

        Args:
            invoice_number (str): Invoice number
            status (str): New status (active, paid, cancelled, etc.)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            print("❌ CosmosDB not available - cannot update status")
            return False

        try:
            print(f"🔄 Updating invoice {invoice_number} status to '{status}'...")

            # Get existing item
            item = self.container.read_item(
                item=invoice_number, partition_key=invoice_number
            )

            # Update status and modification date
            item["status"] = status
            item["modified_date"] = datetime.now(UTC).isoformat()

            # Replace item
            self.container.replace_item(item=item, body=item)
            print(f"✅ Invoice {invoice_number} status updated to '{status}'")
            return True

        except exceptions.CosmosResourceNotFoundError:
            print(f"⚠️  Invoice {invoice_number} not found for status update")
            return False

        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ HTTP error updating status: {e.status_code} - {e.message}")
            return False

        except Exception as e:
            print(f"❌ Error updating invoice status: {e}")
            return False

    def delete_invoice(self, invoice_number: str) -> bool:
        """
        Delete invoice from CosmosDB.

        Args:
            invoice_number (str): Invoice number to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            print("❌ CosmosDB not available - cannot delete invoice")
            return False

        try:
            print(f"🔄 Deleting invoice {invoice_number}...")
            self.container.delete_item(
                item=invoice_number, partition_key=invoice_number
            )
            print(f"✅ Invoice {invoice_number} deleted successfully")
            return True

        except exceptions.CosmosResourceNotFoundError:
            print(f"⚠️  Invoice {invoice_number} not found for deletion")
            return False

        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ HTTP error deleting invoice: {e.status_code} - {e.message}")
            return False

        except Exception as e:
            print(f"❌ Error deleting invoice: {e}")
            return False

    def get_invoice_statistics(self) -> Dict:
        """
        Get comprehensive invoice statistics with optimized aggregation queries.

        Returns:
            Dict: Statistics including counts, totals, and breakdowns
        """
        if not self.is_available():
            return {
                "total_invoices": 0,
                "status_breakdown": [],
                "total_outstanding_amount": 0.0,
                "error": "CosmosDB not available",
            }

        try:
            print("🔄 Calculating invoice statistics...")

            # Get all invoices and calculate locally (more reliable than complex aggregation)
            all_invoices_query = """
                SELECT c.id, c.invoice_number, c.status, c.total, c._ts
                FROM c 
                WHERE c.invoice_number != null
                ORDER BY c._ts DESC
            """

            # Execute query to get all invoices
            all_invoices = list(
                self.container.query_items(
                    query=all_invoices_query,
                    enable_cross_partition_query=True,
                )
            )

            # Calculate statistics locally
            total_invoices = len(all_invoices)
            status_counts = {}
            total_outstanding = 0.0
            total_amount = 0.0

            # Calculate timestamp for last 30 days
            import time
            recent_timestamp = int(time.time()) - (30 * 24 * 60 * 60)
            recent_count = 0

            for invoice in all_invoices:
                # Status breakdown
                status = invoice.get("status", "unknown")
                if status not in status_counts:
                    status_counts[status] = {"count": 0, "total_amount": 0.0}
                
                invoice_total = float(invoice.get("total", 0))
                status_counts[status]["count"] += 1
                status_counts[status]["total_amount"] += invoice_total
                total_amount += invoice_total

                # Outstanding amount (everything except 'paid' status)
                if status != "paid":
                    total_outstanding += invoice_total

                # Recent invoices count
                invoice_ts = invoice.get("_ts", 0)
                if invoice_ts > recent_timestamp:
                    recent_count += 1

            # Format status breakdown
            status_breakdown = [
                {
                    "status": status,
                    "count": data["count"],
                    "total_amount": round(data["total_amount"], 2)
                }
                for status, data in status_counts.items()
            ]

            statistics = {
                "total_invoices": total_invoices,
                "status_breakdown": status_breakdown,
                "total_outstanding_amount": round(total_outstanding, 2),
                "recent_invoices_30_days": recent_count,
                "average_invoice_amount": round(
                    (total_amount / total_invoices) if total_invoices > 0 else 0, 2
                ),
                "last_updated": datetime.now().isoformat(),
            }

            print(f"✅ Statistics calculated: {total_invoices} total invoices")
            return statistics

        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return {
                "total_invoices": 0,
                "status_breakdown": [],
                "total_outstanding_amount": 0.0,
                "error": f"Statistics calculation failed: {str(e)}",
            }


# Example usage and testing functions
def test_cosmos_service():
    """Test function for CosmosDB service with enhanced diagnostics."""
    print("🧪 Testing CosmosDB Service")
    print("=" * 50)

    service = CosmosDBService()

    if not service.is_available():
        print("❌ CosmosDB service not available - cannot run tests")
        return False

    # Test data
    test_invoice = {
        "invoice_number": f"TEST-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        "invoice_date": "12/01/2024",
        "due_date": "12/31/2024",
        "client": {
            "name": "Test Client Corporation",
            "address": "123 Test Street, Test City, TC 12345",
        },
        "line_items": [
            {
                "description": "Test Service",
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

    print("\n🧪 Test 1: Save Invoice")
    save_success = service.save_invoice(test_invoice)
    print(f"Result: {'✅ PASSED' if save_success else '❌ FAILED'}")

    if save_success:
        print("\n🧪 Test 2: Retrieve Invoice")
        retrieved = service.get_invoice(test_invoice["invoice_number"])
        retrieve_success = retrieved is not None
        print(f"Result: {'✅ PASSED' if retrieve_success else '❌ FAILED'}")

        print("\n🧪 Test 3: List Invoices")
        invoices = service.list_invoices(10)
        list_success = len(invoices) > 0
        print(f"Result: {'✅ PASSED' if list_success else '❌ FAILED'}")

        print("\n🧪 Test 4: Search Invoices")
        search_results = service.search_invoices("Test")
        search_success = len(search_results) > 0
        print(f"Result: {'✅ PASSED' if search_success else '❌ FAILED'}")

        print("\n🧪 Test 5: Update Status")
        status_success = service.update_invoice_status(
            test_invoice["invoice_number"], "paid"
        )
        print(f"Result: {'✅ PASSED' if status_success else '❌ FAILED'}")

        print("\n🧪 Test 6: Statistics")
        stats = service.get_invoice_statistics()
        stats_success = stats.get("total_invoices", 0) > 0
        print(f"Result: {'✅ PASSED' if stats_success else '❌ FAILED'}")

        # Clean up
        print("\n🧹 Cleaning up test invoice...")
        service.delete_invoice(test_invoice["invoice_number"])

    print(f"\n{'='*50}")
    print("✅ CosmosDB service test completed!")
    return True


if __name__ == "__main__":
    test_cosmos_service()
 