"""
Enhanced Invoice Generation System with Azure AI Foundry
========================================================

This system generates professional invoices using Azure AI Foundry with GPT-4o,
saves them to CosmosDB, indexes them in Azure Search, and stores files in Azure Storage.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from azure.ai.agents.models import (
    ListSortOrder,
)
import os
import re

# Import our custom services
import config
from service_manager import get_service_manager


class InvoiceGenerationSystem:
    """Comprehensive invoice generation system using Azure AI Foundry."""

    def __init__(self):
        """Initialize the invoice generation system."""
        try:
            print("🔄 Initializing Invoice Generation System...")

            # Get the centralized service manager
            self.service_manager = get_service_manager()

            # Check service availability
            if not self.service_manager.is_service_available("ai_project"):
                print(
                    "⚠️  AI Project service not available - some features may be limited"
                )

            if not self.service_manager.is_service_available("cosmos"):
                print(
                    "⚠️  CosmosDB service not available - data persistence may be limited"
                )

            print("✅ Invoice Generation System initialized successfully")

        except Exception as e:
            print(f"Error initializing Invoice Generation System: {e}")
            raise

    def generate_invoice(self, order_details: Dict) -> Dict:
        """
        Generate a comprehensive invoice from order details.

        Args:
            order_details (Dict): Order information including client, items, etc.

        Returns:
            Dict: Generated invoice data and metadata
        """
        try:
            print(
                f"Generating invoice for order: {order_details.get('order_id', 'N/A')}"
            )

            # Check if AI services are available
            if not self.service_manager.is_service_available("ai_project"):
                print("AI services not available, using fallback invoice generation")
                return {
                    "success": True,
                    "invoice_data": self._create_fallback_invoice(order_details),
                    "fallback_used": True,
                    **self.service_manager.save_invoice(
                        self._create_fallback_invoice(order_details)
                    ),
                }

            # Get AI client and agent
            ai_client = self.service_manager.get_ai_project_client()
            agent = self.service_manager.get_agent()

            if not agent:
                print("AI agent not available, using fallback invoice generation")
                return {
                    "success": True,
                    "invoice_data": self._create_fallback_invoice(order_details),
                    "fallback_used": True,
                    **self.service_manager.save_invoice(
                        self._create_fallback_invoice(order_details)
                    ),
                }

            # Create a new thread for this invoice generation with timeout
            try:
                thread = ai_client.agents.threads.create()
                print(f"Created thread: {thread.id}")
            except Exception as e:
                print(f"Failed to create thread: {e}")
                return {
                    "success": False,
                    "error": f"Thread creation failed: {str(e)}",
                    "fallback_data": self._create_fallback_invoice(order_details),
                }

            # Prepare the detailed invoice generation request
            invoice_request = self._prepare_invoice_request(order_details)

            # Send message to agent with timeout handling
            try:
                message = ai_client.agents.messages.create(
                    thread_id=thread.id, role="user", content=invoice_request
                )
                print(f"✅ Message sent to agent: {message}")
            except Exception as e:
                print(f"Failed to send message: {e}")
                return {
                    "success": False,
                    "error": f"Message creation failed: {str(e)}",
                    "fallback_data": self._create_fallback_invoice(order_details),
                }

            # Run the agent with timeout and retry logic
            try:
                run = ai_client.agents.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=agent.id,
                    instructions="Generate a professional invoice based on the provided order details. Follow all formatting guidelines and create both PDF and JSON outputs.",
                )
            except Exception as e:
                print(f"Failed to run agent: {e}")
                return {
                    "success": False,
                    "error": f"Agent execution failed: {str(e)}",
                    "fallback_data": self._create_fallback_invoice(order_details),
                }

            if run.status == "failed":
                error_message = f"Invoice generation failed: {run.last_error}"
                print(error_message)
                return {
                    "success": False,
                    "error": error_message,
                    "thread_id": thread.id,
                    "fallback_data": self._create_fallback_invoice(order_details),
                }

            # Retrieve the generated content with timeout
            try:
                messages = ai_client.agents.messages.list(
                    thread_id=thread.id, order=ListSortOrder.ASCENDING
                )
            except Exception as e:
                print(f"Failed to retrieve messages: {e}")
                return {
                    "success": False,
                    "error": f"Message retrieval failed: {str(e)}",
                    "fallback_data": self._create_fallback_invoice(order_details),
                }

            # Process the agent's response
            invoice_result = self._process_agent_response(messages, thread.id)

            if invoice_result["success"]:
                # Always generate HTML copy using template
                html_file_path = self._generate_html_invoice_from_template(
                    invoice_result["invoice_data"]
                )
                if html_file_path:
                    invoice_result["invoice_data"]["html_file_path"] = html_file_path
                    invoice_result["html_generated"] = True
                    print(f"✅ HTML invoice generated: {html_file_path}")
                else:
                    invoice_result["html_generated"] = False
                    print("⚠️ Failed to generate HTML copy")

                # Save using service manager (handles both CosmosDB and Search)
                storage_result = self.service_manager.save_invoice(
                    invoice_result["invoice_data"]
                )

                # Update result with storage status
                invoice_result.update(
                    {
                        **storage_result,
                        "thread_id": thread.id,
                    }
                )

                print(
                    f"Invoice {invoice_result['invoice_data']['invoice_number']} generated successfully"
                )
            else:
                # If AI generation failed, create fallback with HTML
                print("AI generation failed, creating fallback invoice with HTML")
                fallback_invoice = self._create_fallback_invoice(order_details)

                # Save fallback invoice
                storage_result = self.service_manager.save_invoice(fallback_invoice)

                return {
                    "success": True,  # Still successful because we have a fallback
                    "invoice_data": fallback_invoice,
                    "fallback_used": True,
                    "ai_generation_failed": True,
                    **storage_result,
                    "thread_id": thread.id,
                }

            return invoice_result

        except Exception as e:
            error_message = f"Critical error generating invoice: {e}"
            print(error_message)
            return {
                "success": False,
                "error": error_message,
                "fallback_data": self._create_fallback_invoice(order_details),
            }

    def _prepare_invoice_request(self, order_details: Dict) -> str:
        """Prepare a detailed invoice generation request."""

        # Generate unique invoice number
        invoice_number = self._generate_invoice_number()

        request = f"""
Please generate a professional invoice with the following details:

**Invoice Information:**
- Invoice Number: {invoice_number}
- Invoice Date: {datetime.now().strftime('%m/%d/%Y')}
- Due Date: {(datetime.now() + timedelta(days=30)).strftime('%m/%d/%Y')}

**Client Information:**
- Client Name: {order_details.get('client_name', 'N/A')}
- Client Address: {order_details.get('client_address', 'N/A')}
- Client Contact: {order_details.get('client_contact', 'N/A')}
- Client Email: {order_details.get('client_email', 'N/A')}

**Order Details:**
{self._format_order_items(order_details.get('items', []))}

**Additional Information:**
- Purchase Order: {order_details.get('po_number', 'N/A')}
- Project Reference: {order_details.get('project_ref', 'N/A')}
- Tax Rate: {order_details.get('tax_rate', 0.08) * 100}%
- Currency: {order_details.get('currency', 'FCFA')}
- Payment Terms: {order_details.get('payment_terms', 'Net 30')}

**Special Instructions:**
{order_details.get('special_instructions', 'Standard invoice processing')}

Please create:
1. A professional PDF invoice following all styling guidelines
2. A JSON structure containing all invoice data
3. Calculate all totals accurately including taxes
4. Apply professional formatting and branding
5. Include all required business information

Return both the structured data and confirmation of file generation.
"""
        return request

    def _format_order_items(self, items: List[Dict]) -> str:
        """Format order items for the invoice request."""
        if not items:
            return "No items specified"

        formatted_items = []
        for i, item in enumerate(items, 1):
            formatted_items.append(f"""
Item {i}:
- Description: {item.get('description', 'N/A')}
- Quantity: {item.get('quantity', 1)}
- Unit Price: ${item.get('unit_price', 0.00):.2f}
- Total: ${item.get('quantity', 1) * item.get('unit_price', 0.00):.2f}
""")

        return "\n".join(formatted_items)

    def _generate_invoice_number(self) -> str:
        """Generate a unique invoice number with timeout handling."""
        now = datetime.now()

        try:
            # Try to get existing invoices with a thread-safe timeout
            from concurrent.futures import (
                ThreadPoolExecutor,
                TimeoutError as FutureTimeoutError,
            )

            def query_cosmos():
                """Query CosmosDB for existing invoices."""
                # Search for invoices with the current year pattern
                existing_invoices = self.service_manager.search_invoices(
                    f"INV-{now.year}"
                )
                count = len(
                    [
                        inv
                        for inv in existing_invoices
                        if inv.get("invoice_number", "").startswith(f"INV-{now.year}")
                    ]
                )
                return count + 1

            # Use ThreadPoolExecutor with timeout
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(query_cosmos)
                    next_number = future.result(timeout=10)  # 10-second timeout

            except (FutureTimeoutError, Exception) as e:
                print(f"CosmosDB query failed or timed out: {e}")
                # Use timestamp-based fallback
                timestamp = now.strftime("%m%d%H%M%S")
                return f"INV-{now.year}-{timestamp}"

        except Exception as e:
            print(f"Error in invoice number generation, using fallback: {e}")
            # Use timestamp-based fallback
            timestamp = now.strftime("%m%d%H%M%S")
            return f"INV-{now.year}-{timestamp}"

        return f"INV-{now.year}-{next_number:06d}"

    def _process_agent_response(self, messages, thread_id: str) -> Dict:
        """Process the agent's response and extract invoice data."""
        try:
            # Get the last assistant message
            assistant_messages = [msg for msg in messages if msg.role == "assistant"]

            if not assistant_messages:
                return {"success": False, "error": "No response from agent"}

            last_message = assistant_messages[-1]

            # Extract text content
            if last_message.text_messages:
                response_text = last_message.text_messages[-1].text.value
            else:
                return {"success": False, "error": "No text content in agent response"}

            # Look for JSON data in the response
            invoice_data = self._extract_invoice_data_from_response(response_text)

            # Get file attachments if any
            file_paths = []
            if last_message.file_ids:
                for file_id in last_message.file_ids:
                    try:
                        # Download and store the file
                        file_path = self._download_and_store_file(file_id, thread_id)
                        if file_path:
                            file_paths.append(file_path)
                    except Exception as e:
                        print(f"Error handling file {file_id}: {e}")

            return {
                "success": True,
                "invoice_data": invoice_data,
                "response_text": response_text,
                "file_paths": file_paths,
                "file_path": file_paths[0] if file_paths else None,
                "thread_id": thread_id,
            }

        except Exception as e:
            return {"success": False, "error": f"Error processing agent response: {e}"}

    def _extract_invoice_data_from_response(self, response_text: str) -> Dict:
        """Extract structured invoice data from agent response."""
        try:
            # Look for JSON blocks in the response
            import re
            import json

            json_pattern = r"```json\s*(.*?)\s*```"
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            if json_matches:
                # Try to parse each JSON block found
                for json_text in json_matches:
                    try:
                        # Clean the JSON text
                        json_text = json_text.strip()
                        if json_text:
                            invoice_data = json.loads(json_text)
                            # Validate that it looks like invoice data
                            if isinstance(invoice_data, dict) and (
                                "invoice_number" in invoice_data
                                or "client" in invoice_data
                            ):
                                return invoice_data
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON block: {e}")
                        continue

            # Try to find any JSON-like structure in the response
            json_like_pattern = r'\{[^}]*"invoice_number"[^}]*\}'
            json_like_matches = re.findall(json_like_pattern, response_text, re.DOTALL)

            for json_text in json_like_matches:
                try:
                    invoice_data = json.loads(json_text)
                    if isinstance(invoice_data, dict):
                        return invoice_data
                except json.JSONDecodeError:
                    continue

            # If no valid JSON found, create fallback data with extracted fields
            print("No valid JSON found in response, using fallback extraction")

            # Extract invoice number with fallback generation
            invoice_number = self._extract_field(
                response_text, "invoice.number", "Invoice Number", "Invoice No"
            )
            if not invoice_number:
                invoice_number = self._generate_invoice_number()

            # Extract client information
            client_name = self._extract_field(
                response_text, "client", "Client Name", "Customer Name"
            )
            client_address = self._extract_field(
                response_text, "address", "Client Address", "Address"
            )

            invoice_data = {
                "invoice_number": invoice_number,
                "invoice_date": datetime.now().strftime("%m/%d/%Y"),
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y"),
                "client": {
                    "name": client_name or "Client Name Required",
                    "address": client_address or "Address Required",
                },
                "line_items": [],
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "total": 0.0,
                "status": "draft",
                "currency": "FCFA",
            }

            return invoice_data

        except Exception as e:
            print(f"Error extracting invoice data: {e}")
            # Return safe fallback data
            return {
                "invoice_number": self._generate_invoice_number(),
                "invoice_date": datetime.now().strftime("%m/%d/%Y"),
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y"),
                "client": {
                    "name": "Data Extraction Error",
                    "address": "Please check source data",
                },
                "line_items": [],
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "total": 0.0,
                "status": "draft",
                "currency": "FCFA",
                "error": f"Could not parse invoice data: {str(e)}",
            }

    def _extract_field(self, text: str, *field_names) -> str:
        """Extract a field value from text using multiple possible field names."""
        import re

        for field_name in field_names:
            # Try different patterns for field extraction
            patterns = [
                rf"{field_name}[:\s]+([^\n\r]+)",  # Field: Value
                rf"{field_name}[:\s]*[\"']([^\"'\n\r]+)[\"']",  # Field: "Value"
                rf'"{field_name}"[:\s]*[\"\']*([^\"\'",\n\r]+)[\"\']*',  # "Field": Value
                rf"{field_name}[:\s]*=\s*([^\n\r]+)",  # Field = Value
            ]

            for pattern in patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        result = match.group(1).strip()
                        # Clean up common artifacts
                        result = re.sub(
                            r'^["\'\s]+|["\'\s]+$', "", result
                        )  # Remove quotes and spaces
                        if result and result.lower() not in [
                            "",
                            "null",
                            "none",
                            "undefined",
                        ]:
                            return result
                except re.error:
                    continue
        return ""

    def _download_and_store_file(self, file_id: str, thread_id: str) -> Optional[str]:
        """Download file from AI service and store in Azure Storage."""
        try:
            # Get AI client
            ai_client = self.service_manager.get_ai_project_client()
            if not ai_client:
                return None

            # Get file content from AI service
            file_content = ai_client.agents.files.get_file_content(file_id)

            # Get file info
            file_info = ai_client.agents.files.get_file(file_id)
            filename = file_info.filename or f"invoice_{file_id}.pdf"

            # Create blob path
            blob_name = f"invoices/{datetime.now().strftime('%Y/%m')}/{filename}"

            # Upload to Azure Storage using service manager
            blob_service = self.service_manager.get_blob_service()
            if blob_service:
                blob_client = blob_service.get_blob_client(
                    container=config.STORAGE_CONTAINER_NAME, blob=blob_name
                )

                blob_client.upload_blob(file_content, overwrite=True)
                print(f"File stored in Azure Storage: {blob_name}")

                return blob_name

            return None

        except Exception as e:
            print(f"Error downloading and storing file: {e}")
            return None

    def list_invoices(self, limit: int = 50) -> List[Dict]:
        """List recent invoices using service manager."""
        return self.service_manager.list_invoices(limit)

    def search_invoices(self, query: str) -> List[Dict]:
        """Search invoices using service manager."""
        return self.service_manager.search_invoices(query)

    def get_invoice(self, invoice_number: str) -> Optional[Dict]:
        """Get a specific invoice by number using service manager."""
        return self.service_manager.get_invoice(invoice_number)

    def update_invoice_status(self, invoice_number: str, status: str) -> bool:
        """Update invoice status using service manager."""
        return self.service_manager.update_invoice_status(invoice_number, status)

    def get_statistics(self) -> Dict:
        """Get invoice statistics using service manager."""
        return self.service_manager.get_statistics()

    def _create_fallback_invoice(self, order_details: Dict) -> Dict:
        """Create a fallback invoice when AI generation fails using HTML template."""
        try:
            # Generate basic invoice data without AI
            invoice_number = self._generate_invoice_number_fallback()

            # Calculate totals from order details with safety checks
            items = order_details.get("items", [])
            subtotal = 0.0

            for item in items:
                try:
                    quantity = (
                        float(item.get("quantity", 0))
                        if item.get("quantity") is not None
                        else 0.0
                    )
                    unit_price = (
                        float(item.get("unit_price", 0))
                        if item.get("unit_price") is not None
                        else 0.0
                    )
                    subtotal += quantity * unit_price
                except (ValueError, TypeError):
                    # Skip items with invalid data
                    continue

            tax_rate = order_details.get("tax_rate", 0.08)
            try:
                tax_rate = float(tax_rate) if tax_rate is not None else 0.08
            except (ValueError, TypeError):
                tax_rate = 0.08

            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount

            fallback_invoice = {
                "invoice_number": invoice_number,
                "invoice_date": datetime.now().strftime("%m/%d/%Y"),
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y"),
                "client": {
                    "name": order_details.get("client_name", "Unknown Client"),
                    "address": order_details.get(
                        "client_address", "Address not provided"
                    ),
                    "contact": order_details.get("client_contact", ""),
                    "email": order_details.get("client_email", ""),
                },
                "line_items": items,
                "subtotal": subtotal,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total": total,
                "currency": order_details.get("currency", "FCFA"),
                "payment_terms": order_details.get("payment_terms", "Net 30"),
                "po_number": order_details.get("po_number", ""),
                "project_ref": order_details.get("project_ref", ""),
                "special_instructions": order_details.get("special_instructions", ""),
                "status": "draft",
                "generated_by": "fallback_system",
                "notes": "Generated using fallback system due to AI service unavailability",
            }

            # Generate HTML invoice using template
            html_file_path = self._generate_html_invoice_from_template(fallback_invoice)
            if html_file_path:
                fallback_invoice["html_file_path"] = html_file_path
                fallback_invoice["file_generated"] = True
                print(f"✅ Fallback HTML invoice generated: {html_file_path}")
            else:
                fallback_invoice["file_generated"] = False
                print("⚠️ Failed to generate HTML file for fallback invoice")

            print(f"Created fallback invoice: {invoice_number}")
            return fallback_invoice

        except Exception as e:
            print(f"Error creating fallback invoice: {e}")
            return {
                "invoice_number": f"FALLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "error": "Could not create fallback invoice",
                "generated_by": "emergency_fallback",
            }

    def _generate_html_invoice_from_template(self, invoice_data: Dict) -> Optional[str]:
        """Generate HTML invoice using the DEMO template as base."""
        try:
            # Read the template file
            template_path = "generated_invoices/DEMO-20250525010320.html"

            if not os.path.exists(template_path):
                print(f"⚠️ Template file not found: {template_path}")
                return None

            with open(template_path, "r", encoding="utf-8") as f:
                template_html = f.read()

            # Replace template data with actual invoice data
            html_content = self._populate_html_template(template_html, invoice_data)

            # Generate output filename
            invoice_number = invoice_data.get("invoice_number", "UNKNOWN")
            safe_invoice_number = re.sub(r"[^\w\-_]", "_", invoice_number)
            output_filename = f"{safe_invoice_number}.html"
            output_path = os.path.join("generated_invoices", output_filename)

            # Ensure directory exists
            os.makedirs("generated_invoices", exist_ok=True)

            # Write the generated HTML
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"📄 HTML invoice generated: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error generating HTML invoice from template: {e}")
            return None

    def _populate_html_template(self, template_html: str, invoice_data: Dict) -> str:
        """Populate HTML template with actual invoice data."""
        try:
            html = template_html

            # Replace invoice details
            html = html.replace(
                "DEMO-20250525010320", invoice_data.get("invoice_number", "UNKNOWN")
            )
            html = html.replace("12/01/2024", invoice_data.get("invoice_date", ""))
            html = html.replace("12/31/2024", invoice_data.get("due_date", ""))
            html = html.replace("Net 30", invoice_data.get("payment_terms", "Net 30"))
            html = html.replace("PO-2024-12345", invoice_data.get("po_number", ""))
            html = html.replace(
                "Website Redesign Project", invoice_data.get("project_ref", "")
            )

            # Replace client information
            client = invoice_data.get("client", {})
            html = html.replace(
                "Acme Corporation", client.get("name", "Unknown Client")
            )
            html = html.replace(
                "456 Business Avenue, Suite 200, Corporate City, CC 67890",
                client.get("address", "Address not provided"),
            )
            html = html.replace(
                "John Smith, Procurement Manager", client.get("contact", "")
            )
            html = html.replace("john.smith@acmecorp.com", client.get("email", ""))

            # Generate line items HTML
            currency = invoice_data.get("currency", "USD")
            line_items_html = self._generate_line_items_html(
                invoice_data.get("line_items", []), currency
            )

            # Replace the line items section (find the tbody and replace its content)
            tbody_pattern = r"<tbody>(.*?)</tbody>"
            html = re.sub(
                tbody_pattern,
                f"<tbody>\n{line_items_html}\n            </tbody>",
                html,
                flags=re.DOTALL,
            )

            # Replace totals
            subtotal = invoice_data.get("subtotal", 0)
            tax_rate = invoice_data.get("tax_rate", 0) * 100  # Convert to percentage
            tax_amount = invoice_data.get("tax_amount", 0)
            total = invoice_data.get("total", 0)
            currency = invoice_data.get("currency", "USD")

            # Format currency properly
            if currency == "USD":
                currency_symbol = "$"
                subtotal_str = f"${subtotal:.2f}"
                tax_str = f"${tax_amount:.2f}"
                total_str = f"${total:.2f} USD"
            elif currency == "FCFA":
                currency_symbol = ""
                subtotal_str = f"{subtotal:.0f} FCFA"
                tax_str = f"{tax_amount:.0f} FCFA"
                total_str = f"{total:.0f} FCFA"
            else:
                currency_symbol = ""
                subtotal_str = f"{subtotal:.2f} {currency}"
                tax_str = f"{tax_amount:.2f} {currency}"
                total_str = f"{total:.2f} {currency}"

            html = html.replace("$6300.00", subtotal_str)
            html = html.replace("8.0%", f"{tax_rate:.1f}%")
            html = html.replace("$504.00", tax_str)
            html = html.replace("$6804.00 USD", total_str)

            # Replace special instructions
            special_instructions = invoice_data.get("special_instructions", "")
            if special_instructions:
                html = html.replace(
                    "Please process payment within 30 days. Contact billing@professionalservices.com for any questions.",
                    special_instructions,
                )

            # Update title
            html = html.replace(
                "Invoice DEMO-20250525010320",
                f"Invoice {invoice_data.get('invoice_number', 'UNKNOWN')}",
            )

            return html

        except Exception as e:
            print(f"Error populating HTML template: {e}")
            return template_html  # Return original template if population fails

    def _generate_line_items_html(self, line_items: List[Dict], currency: str) -> str:
        """Generate HTML for line items table rows."""
        try:
            rows = []
            for item in line_items:
                description = item.get("description", "Unknown Item")
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)
                total = float(quantity) * float(unit_price)

                if currency == "FCFA":
                    unit_price_str = f"{unit_price:.0f} FCFA"
                    total_str = f"{total:.0f} FCFA"
                elif currency == "USD":
                    unit_price_str = f"${unit_price:.2f}"
                    total_str = f"${total:.2f}"
                else:
                    unit_price_str = f"{unit_price:.2f} {currency}"
                    total_str = f"{total:.2f} {currency}"

                row_html = f"""            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">{description}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">{quantity}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">{unit_price_str}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold;">{total_str}</td>
            </tr>"""
                rows.append(row_html)

            return "\n".join(rows)

        except Exception as e:
            print(f"Error generating line items HTML: {e}")
            return ""

    def _generate_invoice_number_fallback(self) -> str:
        """Generate invoice number with fallback for when CosmosDB is slow/unavailable."""
        try:
            # Try quick local generation first
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d%H%M%S")
            return f"INV-{now.year}-{timestamp}"

        except Exception as e:
            print(f"Error in fallback invoice number generation: {e}")
            return f"INV-EMERGENCY-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def main():
    """Main function demonstrating the invoice generation system."""
    try:
        # Initialize the system
        invoice_system = InvoiceGenerationSystem()

        # Example order details
        sample_order = {
            "order_id": "ORD-2024-001",
            "client_name": "Acme Corporation",
            "client_address": "456 Business Avenue, Suite 200, Corporate City, CC 67890",
            "client_contact": "John Smith, Procurement Manager",
            "client_email": "john.smith@acmecorp.com",
            "po_number": "PO-2024-12345",
            "project_ref": "Website Redesign Project",
            "items": [
                {
                    "description": "Web Design and Development Services",
                    "quantity": 40,
                    "unit_price": 125.00,
                },
                {
                    "description": "Content Management System Setup",
                    "quantity": 1,
                    "unit_price": 800.00,
                },
                {
                    "description": "SEO Optimization Package",
                    "quantity": 1,
                    "unit_price": 500.00,
                },
            ],
            "tax_rate": 0.19,
            "currency": "FCFA",
            "payment_terms": "Net 30",
            "special_instructions": "Please process payment within 30 days. Contact billing@professionalservices.com for any questions.",
        }

        # Generate invoice
        print("Generating sample invoice...")
        result = invoice_system.generate_invoice(sample_order)

        if result["success"]:
            print("✅ Invoice generated successfully!")
            print(f"Invoice Number: {result['invoice_data']['invoice_number']}")
            print(f"CosmosDB Saved: {result['cosmos_saved']}")
            print(f"Search Indexed: {result['search_indexed']}")
            print(f"Thread ID: {result['thread_id']}")

            if result.get("file_paths"):
                print(f"Files generated: {', '.join(result['file_paths'])}")
        else:
            print(f"❌ Invoice generation failed: {result['error']}")

        # Demonstrate search functionality
        print("\nTesting search functionality...")
        search_results = invoice_system.search_invoices("Acme")
        print(f"Found {len(search_results)} invoices matching 'Acme'")

        # Show statistics
        print("\nInvoice Statistics:")
        stats = invoice_system.get_statistics()
        print(f"Total Invoices: {stats.get('total_invoices', 0)}")
        print(f"Outstanding Amount: ${stats.get('total_outstanding_amount', 0):,.2f}")

    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()
