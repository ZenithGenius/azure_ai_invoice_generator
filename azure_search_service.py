"""
Azure AI Search Service for Invoice Management
=============================================

This module handles Azure AI Search operations for indexing and searching invoices.
"""

from datetime import datetime
from typing import Dict, List
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import config


class AzureSearchService:
    """Service class for managing invoice search with Azure AI Search."""

    def __init__(self):
        """Initialize the Azure Search service."""
        try:
            # Initialize credentials
            if config.SEARCH_KEY:
                credential = AzureKeyCredential(config.SEARCH_KEY)
            else:
                credential = DefaultAzureCredential()

            # Initialize clients with timeout settings
            self.search_client = SearchClient(
                endpoint=config.SEARCH_ENDPOINT,
                index_name=config.SEARCH_INDEX_NAME,
                credential=credential,
            )

            self.index_client = SearchIndexClient(
                endpoint=config.SEARCH_ENDPOINT, credential=credential
            )

            # Create index if it doesn't exist
            self._create_invoice_index()
            self.available = True

        except Exception as e:
            print(f"Error initializing Azure Search service: {e}")
            print("System will continue with limited search functionality")
            self.search_client = None
            self.index_client = None
            self.available = False

    def _create_invoice_index(self):
        """Create the invoice search index if it doesn't exist."""
        try:
            # Define the index schema
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SimpleField(
                    name="invoice_number",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="invoice_date",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="due_date",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="status", type=SearchFieldDataType.String, filterable=True
                ),
                SimpleField(
                    name="total_amount",
                    type=SearchFieldDataType.Double,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="currency", type=SearchFieldDataType.String, filterable=True
                ),
                # Client information
                SearchableField(
                    name="client_name",
                    type=SearchFieldDataType.String,
                    analyzer_name="standard.lucene",
                ),
                SearchableField(
                    name="client_address",
                    type=SearchFieldDataType.String,
                    analyzer_name="standard.lucene",
                ),
                SearchableField(name="client_contact", type=SearchFieldDataType.String),
                # Line items as searchable text
                SearchableField(
                    name="line_items_text",
                    type=SearchFieldDataType.String,
                    analyzer_name="standard.lucene",
                ),
                # Full invoice content for search
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    analyzer_name="standard.lucene",
                ),
                # Metadata
                SimpleField(
                    name="created_date",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="modified_date",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
                # File information
                SimpleField(name="file_path", type=SearchFieldDataType.String),
                SimpleField(name="file_size", type=SearchFieldDataType.Int64),
                # Tags for categorization
                SearchableField(
                    name="tags",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    filterable=True,
                ),
            ]

            # Create index
            index = SearchIndex(name=config.SEARCH_INDEX_NAME, fields=fields)

            try:
                result = self.index_client.create_index(index)
                print(f"Created search index: {config.SEARCH_INDEX_NAME}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"Search index {config.SEARCH_INDEX_NAME} already exists")
                else:
                    raise

        except Exception as e:
            print(f"Error creating search index: {e}")
            raise

    def index_invoice(self, invoice_data: Dict, file_path: str = None) -> bool:
        """
        Index an invoice for search.

        Args:
            invoice_data (Dict): Invoice data to index
            file_path (str): Optional file path for the generated PDF

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.available or not self.search_client:
            print("Azure Search not available - cannot index invoice")
            return False

        try:
            # Prepare search document
            search_doc = {
                "id": invoice_data.get("invoice_number"),
                "invoice_number": invoice_data.get("invoice_number"),
                "invoice_date": self._parse_date(invoice_data.get("invoice_date")),
                "due_date": self._parse_date(invoice_data.get("due_date")),
                "status": "active",
                "total_amount": invoice_data.get("total", 0),
                "currency": invoice_data.get("currency", "USD"),
                # Client information
                "client_name": invoice_data.get("client", {}).get("name", ""),
                "client_address": invoice_data.get("client", {}).get("address", ""),
                "client_contact": invoice_data.get("client", {}).get("contact", ""),
                # Line items as searchable text
                "line_items_text": self._format_line_items(
                    invoice_data.get("line_items", [])
                ),
                # Full content for search
                "content": self._create_search_content(invoice_data),
                # Metadata
                "created_date": datetime.utcnow().isoformat(),
                "modified_date": datetime.utcnow().isoformat(),
                # File information
                "file_path": file_path or "",
                "file_size": 0,  # Will be updated if file exists
                # Tags
                "tags": self._generate_tags(invoice_data),
            }

            # Upload document to search index
            result = self.search_client.upload_documents([search_doc])

            if result[0].succeeded:
                print(
                    f"Invoice {invoice_data.get('invoice_number')} indexed successfully"
                )
                return True
            else:
                print(f"Failed to index invoice: {result[0].error_message}")
                return False

        except Exception as e:
            print(f"Error indexing invoice: {e}")
            return False

    def search_invoices(
        self, query: str, filters: str = None, top: int = 50
    ) -> List[Dict]:
        """
        Search invoices using text query.

        Args:
            query (str): Search query
            filters (str): Optional OData filter expression
            top (int): Maximum number of results to return

        Returns:
            List[Dict]: List of search results
        """
        if not self.available or not self.search_client:
            print("Azure Search not available - cannot search invoices")
            return []

        try:
            results = self.search_client.search(
                search_text=query,
                filter=filters,
                top=top,
                include_total_count=True,
                highlight_fields="client_name,line_items_text",
            )

            search_results = []
            for result in results:
                search_results.append(
                    {
                        "score": result["@search.score"],
                        "invoice_number": result.get("invoice_number"),
                        "client_name": result.get("client_name"),
                        "invoice_date": result.get("invoice_date"),
                        "total_amount": result.get("total_amount"),
                        "status": result.get("status"),
                        "highlights": result.get("@search.highlights", {}),
                    }
                )

            return search_results

        except Exception as e:
            print(f"Error searching invoices: {e}")
            return []

    def filter_invoices(self, filters: Dict) -> List[Dict]:
        """
        Filter invoices using structured filters.

        Args:
            filters (Dict): Filter criteria

        Returns:
            List[Dict]: List of filtered results
        """
        try:
            filter_expressions = []

            # Build filter expressions
            if filters.get("client_name"):
                filter_expressions.append(
                    f"search.ismatch('{filters['client_name']}', 'client_name')"
                )

            if filters.get("status"):
                filter_expressions.append(f"status eq '{filters['status']}'")

            if filters.get("date_from"):
                filter_expressions.append(f"invoice_date ge {filters['date_from']}")

            if filters.get("date_to"):
                filter_expressions.append(f"invoice_date le {filters['date_to']}")

            if filters.get("amount_min"):
                filter_expressions.append(f"total_amount ge {filters['amount_min']}")

            if filters.get("amount_max"):
                filter_expressions.append(f"total_amount le {filters['amount_max']}")

            # Combine filters
            filter_string = (
                " and ".join(filter_expressions) if filter_expressions else None
            )

            # Execute search
            results = self.search_client.search(
                search_text="*",
                filter=filter_string,
                order_by=["invoice_date desc"],
                top=100,
            )

            return [dict(result) for result in results]

        except Exception as e:
            print(f"Error filtering invoices: {e}")
            return []

    def get_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions based on partial query.

        Args:
            query (str): Partial search query

        Returns:
            List[str]: List of suggestions
        """
        try:
            # Use autocomplete functionality if available
            results = self.search_client.search(
                search_text=f"{query}*",
                search_mode="any",
                top=10,
                select=["client_name", "invoice_number"],
            )

            suggestions = []
            for result in results:
                if result.get("client_name"):
                    suggestions.append(result["client_name"])
                if result.get("invoice_number"):
                    suggestions.append(result["invoice_number"])

            return list(set(suggestions))  # Remove duplicates

        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []

    def delete_invoice_from_index(self, invoice_number: str) -> bool:
        """
        Delete invoice from search index.

        Args:
            invoice_number (str): Invoice number to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.search_client.delete_documents([{"id": invoice_number}])

            if result[0].succeeded:
                print(f"Invoice {invoice_number} deleted from search index")
                return True
            else:
                print(f"Failed to delete invoice from index: {result[0].error_message}")
                return False

        except Exception as e:
            print(f"Error deleting invoice from search index: {e}")
            return False

    def update_invoice_status_in_index(self, invoice_number: str, status: str) -> bool:
        """
        Update invoice status in search index.

        Args:
            invoice_number (str): Invoice number
            status (str): New status

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Merge update (partial update)
            update_doc = {
                "id": invoice_number,
                "status": status,
                "modified_date": datetime.utcnow().isoformat(),
            }

            result = self.search_client.merge_documents([update_doc])

            if result[0].succeeded:
                print(f"Invoice {invoice_number} status updated in search index")
                return True
            else:
                print(
                    f"Failed to update invoice status in index: {result[0].error_message}"
                )
                return False

        except Exception as e:
            print(f"Error updating invoice status in search index: {e}")
            return False

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO format with timezone for Azure Search."""
        if not date_str:
            return None
        try:
            # Handle MM/DD/YYYY format
            if "/" in date_str:
                dt = datetime.strptime(date_str, "%m/%d/%Y")
                # Add timezone info for Azure Search DateTimeOffset
                return dt.replace(tzinfo=datetime.now().astimezone().tzinfo).isoformat()

            # Handle ISO format strings
            if "T" in date_str:
                # Parse existing ISO format
                if (
                    date_str.endswith("Z")
                    or "+" in date_str[-6:]
                    or date_str[-6:].count(":") == 2
                ):
                    return date_str  # Already has timezone
                else:
                    # Add timezone to ISO format without timezone
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    return dt.replace(
                        tzinfo=datetime.now().astimezone().tzinfo
                    ).isoformat()

            return date_str
        except Exception as e:
            print(f"Date parsing error for '{date_str}': {e}")
            # Return current time with timezone as fallback
            return datetime.now().astimezone().isoformat()

    def _format_line_items(self, line_items: List[Dict]) -> str:
        """Format line items as searchable text."""
        text_parts = []
        for item in line_items:
            description = item.get("description", "")
            quantity = item.get("quantity", 0)
            price = item.get("unit_price", 0)
            text_parts.append(f"{description} (Qty: {quantity}, Price: ${price})")
        return " | ".join(text_parts)

    def _create_search_content(self, invoice_data: Dict) -> str:
        """Create comprehensive search content from invoice data."""
        content_parts = []

        # Add invoice details
        content_parts.append(f"Invoice {invoice_data.get('invoice_number', '')}")
        content_parts.append(f"Date: {invoice_data.get('invoice_date', '')}")

        # Add client information
        client = invoice_data.get("client", {})
        content_parts.append(f"Client: {client.get('name', '')}")
        content_parts.append(f"Address: {client.get('address', '')}")

        # Add line items
        for item in invoice_data.get("line_items", []):
            content_parts.append(item.get("description", ""))

        # Add amounts
        content_parts.append(f"Total: ${invoice_data.get('total', 0)}")

        return " ".join(content_parts)

    def _generate_tags(self, invoice_data: Dict) -> List[str]:
        """Generate tags for invoice categorization."""
        tags = []

        # Add client-based tags
        client_name = invoice_data.get("client", {}).get("name", "")
        if client_name:
            tags.append(client_name.lower())

        # Add amount-based tags
        total = invoice_data.get("total", 0)
        if total > 10000:
            tags.append("high-value")
        elif total > 1000:
            tags.append("medium-value")
        else:
            tags.append("low-value")

        # Add date-based tags
        invoice_date = invoice_data.get("invoice_date", "")
        if invoice_date:
            try:
                dt = datetime.strptime(invoice_date, "%m/%d/%Y")
                tags.append(f"year-{dt.year}")
                tags.append(f"month-{dt.month:02d}")
                tags.append(f"quarter-q{(dt.month-1)//3 + 1}")
            except:
                pass

        return tags


# Example usage and testing
def test_search_service():
    """Test function for Azure Search service."""
    service = AzureSearchService()

    # Test data
    test_invoice = {
        "invoice_number": "INV-2024-000001",
        "invoice_date": "12/01/2024",
        "due_date": "12/31/2024",
        "client": {
            "name": "Test Client Corp",
            "address": "123 Test Street, Test City, TC 12345",
            "contact": "test@testclient.com",
        },
        "line_items": [
            {
                "description": "Professional Consulting Services",
                "quantity": 10,
                "unit_price": 150.00,
                "total": 1500.00,
            }
        ],
        "subtotal": 1500.00,
        "tax_rate": 0.08,
        "tax_amount": 120.00,
        "total": 1620.00,
    }

    # Test indexing
    success = service.index_invoice(test_invoice)
    print(f"Index test: {'PASSED' if success else 'FAILED'}")

    # Test searching
    results = service.search_invoices("Test Client")
    print(f"Search test: {'PASSED' if len(results) > 0 else 'FAILED'}")

    return service


if __name__ == "__main__":
    test_search_service()
