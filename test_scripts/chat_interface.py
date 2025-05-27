"""
Invoice Management Chat Interface - Terminal Edition
===================================================

Simple terminal-based chat interface for invoice management.
"""

import sys
from datetime import datetime
from service_manager import get_service_manager


class InvoiceChatAgent:
    """Simple terminal-based chat agent for invoice management."""

    def __init__(self):
        """Initialize the chat agent."""
        print("🔄 Initializing Invoice Chat Agent...")
        self.service_manager = get_service_manager()
        print("✅ Invoice Chat Agent initialized successfully")

    def start_chat(self):
        """Start the interactive chat session."""
        print("\n" + "=" * 60)
        print("🤖 Invoice Management Chat Agent")
        print("=" * 60)
        print("Type 'help' for available commands or 'quit' to exit")
        print()

        while True:
            try:
                user_input = input("💬 You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("👋 Goodbye! Thanks for using the Invoice Chat Agent.")
                    break

                response = self.process_input(user_input)
                print(f"🤖 Agent: {response}\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye! Thanks for using the Invoice Chat Agent.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def process_input(self, user_input: str) -> str:
        """Process user input and return appropriate response."""
        user_input = user_input.lower().strip()

        # Help command
        if "help" in user_input:
            return self.get_help_message()

        # Statistics
        elif any(word in user_input for word in ["stats", "statistics", "summary"]):
            return self.handle_statistics()

        # List invoices
        elif any(word in user_input for word in ["list", "show", "recent"]):
            return self.handle_list_invoices()

        # Search
        elif any(word in user_input for word in ["search", "find"]):
            return self.handle_search(user_input)

        # Create invoice
        elif any(word in user_input for word in ["create", "generate", "new"]):
            return self.handle_create_invoice(user_input)

        # Default response
        else:
            return "🤔 I didn't understand that. Type 'help' for available commands."

    def handle_statistics(self) -> str:
        """Handle statistics request."""
        try:
            stats = self.service_manager.get_statistics()

            response = f"""
📊 Invoice Statistics:
• Total Invoices: {stats.get('total_invoices', 0)}
• Outstanding Amount: ${stats.get('total_outstanding_amount', 0):,.2f}

📋 Status Breakdown:"""

            if stats.get("status_breakdown"):
                for status_info in stats["status_breakdown"]:
                    status = status_info.get("status", "Unknown").title()
                    count = status_info.get("count", 0)
                    response += f"\n  • {status}: {count} invoices"

            return response

        except Exception as e:
            return f"❌ Error getting statistics: {e}"

    def handle_list_invoices(self) -> str:
        """Handle list invoices request."""
        try:
            invoices = self.service_manager.list_invoices(limit=5)

            if not invoices:
                return "📭 No invoices found."

            response = f"📋 Recent Invoices ({len(invoices)} shown):\n"

            for invoice in invoices:
                invoice_data = invoice.get("invoice_data", {})
                client = invoice_data.get("client", {}).get("name", "Unknown")
                amount = invoice_data.get("total", 0)
                status = invoice.get("status", "Unknown").title()

                response += f"  • {invoice.get('invoice_number', 'N/A')} - {client} - ${amount:.2f} ({status})\n"

            return response

        except Exception as e:
            return f"❌ Error listing invoices: {e}"

    def handle_search(self, user_input: str) -> str:
        """Handle search request."""
        # Extract search term
        words = user_input.split()
        search_words = [w for w in words if w not in ["search", "find", "for"]]
        search_term = " ".join(search_words) if search_words else "recent"

        try:
            results = self.service_manager.search_invoices(search_term)

            if not results:
                return f"🔍 No invoices found matching '{search_term}'"

            response = f"🔍 Found {len(results)} invoices matching '{search_term}':\n"

            for invoice in results[:5]:  # Show first 5 results
                invoice_data = invoice.get("invoice_data", {})
                client = invoice_data.get("client", {}).get("name", "Unknown")
                amount = invoice_data.get("total", 0)

                response += f"  • {invoice.get('invoice_number', 'N/A')} - {client} - ${amount:.2f}\n"

            if len(results) > 5:
                response += f"  ... and {len(results) - 5} more results"

            return response

        except Exception as e:
            return f"❌ Error searching invoices: {e}"

    def handle_create_invoice(self, user_input: str) -> str:
        """Handle create invoice request."""
        # Extract client name if provided
        words = user_input.split()
        client_name = "Sample Client"

        for i, word in enumerate(words):
            if word.lower() in ["for", "client"] and i + 1 < len(words):
                client_name = " ".join(words[i + 1 : i + 3])  # Take next 1-2 words
                break

        # Create sample invoice
        sample_order = {
            "order_id": f"CHAT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "client_name": client_name,
            "client_address": "123 Business Street, City, State 12345",
            "client_contact": "Contact Person",
            "client_email": "contact@client.com",
            "items": [
                {
                    "description": "Professional Services",
                    "quantity": 1,
                    "unit_price": 500.00,
                }
            ],
            "tax_rate": 0.08,
            "currency": "USD",
            "payment_terms": "Net 30",
            "special_instructions": f"Created via chat on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        }

        try:
            result = self.service_manager.generate_invoice(sample_order)

            if result.get("success"):
                invoice_data = result["invoice_data"]
                return f"""
✅ Invoice created successfully!
📄 Invoice Number: {invoice_data['invoice_number']}
👤 Client: {client_name}
💰 Amount: ${invoice_data.get('total', 0):.2f}
💾 Storage: {'✅ Saved' if result.get('cosmos_saved') else '❌ Failed'}
"""
            else:
                return f"❌ Failed to create invoice: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Error creating invoice: {e}"

    def get_help_message(self) -> str:
        """Return help message."""
        return """
🤖 Invoice Management Chat Agent Help

Available Commands:
• 'stats' or 'statistics' - Show invoice statistics
• 'list' or 'recent' - List recent invoices
• 'search [term]' - Search invoices
• 'create invoice for [client]' - Create new invoice
• 'help' - Show this help message
• 'quit' or 'exit' - Exit the chat

Examples:
• "show me statistics"
• "list recent invoices"
• "search Microsoft"
• "create invoice for Acme Corp"

Just type naturally - I'll understand! 😊
        """


def main():
    """Main function to start the chat agent."""
    try:
        agent = InvoiceChatAgent()
        agent.start_chat()
    except Exception as e:
        print(f"❌ Failed to start chat agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
