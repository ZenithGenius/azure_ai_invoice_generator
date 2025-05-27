"""
Enhanced Invoice Form Component with Queue Integration
====================================================

Provides quick invoice generation with background processing and real-time updates.
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, List, Optional

# Import queue and real-time components
try:
    from components.invoice_queue import get_invoice_queue, JobStatus
    from components.realtime_updates import get_status_updater

    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False
    print("⚠️ Queue system not available - using direct processing")


class InvoiceFormComponent:
    """Enhanced invoice form with queue integration."""

    def __init__(self, service_manager):
        """Initialize the invoice form component."""
        self.service_manager = service_manager

        # Initialize queue and real-time updates if available
        if QUEUE_AVAILABLE:
            self.invoice_queue = get_invoice_queue()
            self.status_updater = get_status_updater()

            # Add status callback for job updates
            self.invoice_queue.add_status_callback(self._handle_job_status_update)
        else:
            self.invoice_queue = None
            self.status_updater = None

    def render_quick_invoice_form(self) -> None:
        """Render the enhanced quick invoice generation form."""
        st.markdown("### 🚀 Quick Invoice Generator")

        # Show queue status if available
        if QUEUE_AVAILABLE and self.invoice_queue:
            self._render_queue_status()

        # Show active jobs if any
        self._render_active_jobs()

        # Handle line item management outside the form
        self._render_line_item_management()

        with st.form("quick_invoice_form", clear_on_submit=False):
            # Client Information Section
            st.markdown("#### 👤 Client Information")
            col1, col2 = st.columns(2)

            with col1:
                client_name = st.text_input(
                    "Client Name *",
                    placeholder="Enter client name",
                    help="Required field",
                )
                client_email = st.text_input(
                    "Client Email", placeholder="client@example.com"
                )

            with col2:
                client_contact = st.text_input(
                    "Contact Number", placeholder="+1 (555) 123-4567"
                )
                po_number = st.text_input(
                    "PO Number", placeholder="Optional purchase order number"
                )

            client_address = st.text_area(
                "Client Address", placeholder="Enter full address", height=80
            )

            # Service/Product Information Section (display only)
            st.markdown("#### 📋 Service/Product Details")

            # Display current line items (read-only in form)
            if "line_items" not in st.session_state:
                st.session_state.line_items = [
                    {"description": "", "quantity": 1, "unit_price": 0.0}
                ]

            for i, item in enumerate(st.session_state.line_items):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    description = st.text_input(
                        f"Description {i+1}",
                        value=item["description"],
                        key=f"desc_{i}",
                        placeholder="Service or product description",
                    )

                with col2:
                    quantity = st.number_input(
                        f"Qty {i+1}",
                        min_value=0.1,
                        value=float(item["quantity"]),
                        step=0.1,
                        key=f"qty_{i}",
                    )

                with col3:
                    unit_price = st.number_input(
                        f"Unit Price {i+1}",
                        min_value=0.0,
                        value=float(item["unit_price"]),
                        step=0.01,
                        key=f"price_{i}",
                    )

                # Update session state
                st.session_state.line_items[i] = {
                    "description": description,
                    "quantity": quantity,
                    "unit_price": unit_price,
                }

            # Invoice Settings Section
            st.markdown("#### ⚙️ Invoice Settings")
            col1, col2, col3 = st.columns(3)

            with col1:
                currency = st.selectbox(
                    "Currency", ["USD", "EUR", "GBP", "FCFA", "CAD", "AUD"], index=0
                )

            with col2:
                tax_rate = (
                    st.number_input(
                        "Tax Rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        step=0.1,
                    )
                    / 100
                )

            with col3:
                payment_terms = st.selectbox(
                    "Payment Terms",
                    ["Net 30", "Net 15", "Net 60", "Due on Receipt", "Custom"],
                    index=0,
                )

            # Additional Information
            col1, col2 = st.columns(2)
            with col1:
                project_ref = st.text_input(
                    "Project Reference", placeholder="Optional project reference"
                )

            with col2:
                # Processing mode selection
                if QUEUE_AVAILABLE:
                    processing_mode = st.selectbox(
                        "Processing Mode",
                        ["Background Queue", "Direct Processing"],
                        index=0,
                        help="Background queue allows you to continue working while invoice is generated",
                    )
                else:
                    processing_mode = "Direct Processing"
                    st.info("Background processing not available - using direct mode")

            notes = st.text_area(
                "Additional Notes",
                placeholder="Any additional notes or terms",
                height=68,
            )

            # Calculate total preview
            total_before_tax = sum(
                item["quantity"] * item["unit_price"]
                for item in st.session_state.line_items
            )
            tax_amount = total_before_tax * tax_rate
            total_amount = total_before_tax + tax_amount

            # Display totals
            st.markdown("#### 💰 Invoice Total Preview")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Subtotal", f"{currency} {total_before_tax:,.2f}")
            with col2:
                st.metric("Tax", f"{currency} {tax_amount:,.2f}")
            with col3:
                st.metric("**Total**", f"{currency} {total_amount:,.2f}")

            # Submit button
            submitted = st.form_submit_button(
                "🚀 Generate Invoice", type="primary", use_container_width=True
            )

            if submitted:
                self._process_invoice_submission(
                    client_name,
                    client_email,
                    client_address,
                    client_contact,
                    po_number,
                    payment_terms,
                    currency,
                    tax_rate,
                    project_ref,
                    notes,
                    processing_mode,
                )

    def _render_queue_status(self):
        """Render queue status information."""
        if not self.invoice_queue:
            return

        queue_stats = self.invoice_queue.get_queue_stats()

        # Show queue metrics in a compact format
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Queue",
                queue_stats["queue_length"],
                help="Jobs waiting to be processed",
            )
        with col2:
            st.metric(
                "Processing",
                queue_stats["processing_jobs"],
                help="Jobs currently being processed",
            )
        with col3:
            st.metric(
                "Completed",
                queue_stats["completed_jobs"],
                help="Successfully completed jobs",
            )
        with col4:
            st.metric(
                "Failed", queue_stats["failed_jobs"], help="Failed jobs (will retry)"
            )

    def _render_active_jobs(self):
        """Render active job status."""
        if "active_jobs" not in st.session_state:
            st.session_state.active_jobs = []

        # Clean up completed jobs older than 5 minutes
        current_time = datetime.now()
        st.session_state.active_jobs = [
            job
            for job in st.session_state.active_jobs
            if (current_time - job.get("created_at", current_time)).total_seconds()
            < 300
        ]

        if st.session_state.active_jobs:
            st.markdown("#### 📊 Active Invoice Jobs")

            for job_info in st.session_state.active_jobs:
                job_id = job_info["job_id"]

                # Get current job status
                if self.invoice_queue:
                    job = self.invoice_queue.get_job_status(job_id)
                    if job:
                        self._render_job_status(job)

    def _render_job_status(self, job):
        """Render individual job status."""
        # Determine status color and icon
        status_config = {
            JobStatus.QUEUED: {
                "color": "blue",
                "icon": "⏳",
                "message": "Waiting in queue",
            },
            JobStatus.PROCESSING: {
                "color": "orange",
                "icon": "🔄",
                "message": "Processing",
            },
            JobStatus.COMPLETED: {
                "color": "green",
                "icon": "✅",
                "message": "Completed",
            },
            JobStatus.FAILED: {"color": "red", "icon": "❌", "message": "Failed"},
            JobStatus.CANCELLED: {
                "color": "gray",
                "icon": "🚫",
                "message": "Cancelled",
            },
        }

        config = status_config.get(
            job.status, {"color": "gray", "icon": "❓", "message": "Unknown"}
        )

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.write(
                    f"{config['icon']} **Job {job.job_id[:8]}...** - {config['message']}"
                )

                # Show progress bar for processing jobs
                if job.status == JobStatus.PROCESSING:
                    st.progress(job.progress, text=f"Progress: {job.progress*100:.0f}%")

            with col2:
                client_name = job.order_details.get("client_name", "Unknown Client")
                st.write(f"👤 {client_name}")

            with col3:
                elapsed = datetime.now() - job.created_at
                st.write(f"⏱️ {elapsed.total_seconds():.0f}s ago")

            with col4:
                if job.status == JobStatus.QUEUED and st.button(
                    "Cancel", key=f"cancel_{job.job_id}"
                ):
                    if self.invoice_queue.cancel_job(job.job_id):
                        st.success("Job cancelled")
                        st.rerun()

            # Show result or error
            if job.status == JobStatus.COMPLETED and job.result:
                invoice_data = job.result.get("invoice_data", {})
                invoice_number = invoice_data.get("invoice_number", "N/A")
                st.success(f"✅ Invoice {invoice_number} generated successfully!")

                # Show download link if available
                if "html_file_path" in invoice_data:
                    st.download_button(
                        "📄 Download Invoice",
                        data=self._get_file_content(invoice_data["html_file_path"]),
                        file_name=f"{invoice_number}.html",
                        mime="text/html",
                        key=f"download_{job.job_id}",
                    )

            elif job.status == JobStatus.FAILED and job.error:
                st.error(f"❌ Error: {job.error}")

                # Show retry option
                if st.button("🔄 Retry", key=f"retry_{job.job_id}"):
                    new_job_id = self.invoice_queue.enqueue_invoice(job.order_details)
                    st.info(f"Retrying as job {new_job_id[:8]}...")
                    st.rerun()

            st.divider()

    def _process_invoice_submission(
        self,
        client_name: str,
        client_email: str,
        client_address: str,
        client_contact: str,
        po_number: str,
        payment_terms: str,
        currency: str,
        tax_rate: float,
        project_ref: str,
        notes: str,
        processing_mode: str = "Direct Processing",
    ) -> None:
        """Process invoice submission with queue or direct processing."""

        # Validation
        if not client_name.strip():
            st.error("❌ Client name is required!")
            return

        # Check if we have at least one valid line item
        valid_items = [
            item
            for item in st.session_state.line_items
            if item["description"].strip()
            and item["quantity"] > 0
            and item["unit_price"] > 0
        ]

        if not valid_items:
            st.error("❌ Please add at least one valid line item!")
            return

        # Prepare order details
        order_details = {
            "client_name": client_name.strip(),
            "client_email": client_email.strip() if client_email else "",
            "client_address": client_address.strip() if client_address else "",
            "client_contact": client_contact.strip() if client_contact else "",
            "po_number": po_number.strip() if po_number else "",
            "payment_terms": payment_terms,
            "currency": currency,
            "tax_rate": tax_rate,
            "project_ref": project_ref.strip() if project_ref else "",
            "notes": notes.strip() if notes else "",
            "items": valid_items,
            "created_via": "quick_form",
            "created_at": datetime.now().isoformat(),
        }

        try:
            if (
                processing_mode == "Background Queue"
                and QUEUE_AVAILABLE
                and self.invoice_queue
            ):
                # Use queue for background processing
                job_id = self.invoice_queue.enqueue_invoice(order_details, priority=1)

                # Add to active jobs tracking
                if "active_jobs" not in st.session_state:
                    st.session_state.active_jobs = []

                st.session_state.active_jobs.append(
                    {
                        "job_id": job_id,
                        "client_name": client_name,
                        "created_at": datetime.now(),
                    }
                )

                # Show success message
                st.success(f"🎉 Invoice generation started! Job ID: {job_id[:8]}...")
                st.info(
                    "💡 You can continue working while the invoice is generated in the background."
                )

                # Send notification
                if self.status_updater:
                    self.status_updater.send_notification(
                        f"Invoice generation started for {client_name}",
                        level="info",
                        data={"job_id": job_id, "client_name": client_name},
                    )

                # Clear form
                self._clear_form()

            else:
                # Direct processing (original method)
                with st.spinner("🔄 Generating invoice..."):
                    result = self.service_manager.generate_invoice(order_details)

                if result.get("success"):
                    invoice_data = result.get("invoice_data", {})
                    invoice_number = invoice_data.get("invoice_number", "N/A")

                    if result.get("fallback_used"):
                        st.success(
                            "🎉 Invoice generated successfully using template system!"
                        )
                        st.info(
                            "💡 AI service was unavailable, but your invoice was created using our reliable template system."
                        )
                    else:
                        st.success("🎉 Invoice generated successfully!")

                    # Show invoice details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Invoice Number", invoice_number)
                    with col2:
                        total = invoice_data.get("total", 0)
                        st.metric("Total Amount", f"{currency} {total:,.2f}")
                    with col3:
                        status = invoice_data.get("status", "Draft")
                        st.metric("Status", status)

                    # Show file path if available
                    if "html_file_path" in invoice_data:
                        st.info(
                            f"📄 Professional HTML invoice created: `{invoice_data['html_file_path']}`"
                        )

                    # Add notification to session state
                    self._add_notification(
                        f"Invoice {invoice_number} generated successfully!", "success"
                    )

                    # Clear form after successful generation
                    self._clear_form()

                else:
                    error_msg = result.get("error", "Unknown error occurred")
                    st.error(f"❌ Failed to generate invoice: {error_msg}")

                    # Show fallback data if available
                    if "fallback_data" in result:
                        st.info(
                            "💡 A fallback invoice was prepared. Please try again or contact support."
                        )

                    self._add_notification(
                        f"Invoice generation failed: {error_msg}", "error"
                    )

        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            self._add_notification(f"Unexpected error: {str(e)}", "error")

    def _handle_job_status_update(self, job):
        """Handle job status updates from the queue."""
        # This callback is triggered when job status changes
        # We can use this to update the UI or send notifications

        if job.status == JobStatus.COMPLETED:
            if self.status_updater:
                client_name = job.order_details.get("client_name", "Unknown")
                invoice_number = job.result.get("invoice_data", {}).get(
                    "invoice_number", "N/A"
                )

                self.status_updater.send_notification(
                    f"Invoice {invoice_number} completed for {client_name}",
                    level="success",
                    data={
                        "job_id": job.job_id,
                        "invoice_number": invoice_number,
                        "client_name": client_name,
                    },
                )

        elif job.status == JobStatus.FAILED:
            if self.status_updater:
                client_name = job.order_details.get("client_name", "Unknown")

                self.status_updater.send_notification(
                    f"Invoice generation failed for {client_name}: {job.error}",
                    level="error",
                    data={
                        "job_id": job.job_id,
                        "error": job.error,
                        "client_name": client_name,
                    },
                )

    def _get_file_content(self, file_path: str) -> str:
        """Get file content for download."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return ""

    def _clear_form(self) -> None:
        """Clear the form after successful submission."""
        # Reset line items to default
        st.session_state.line_items = [
            {"description": "", "quantity": 1, "unit_price": 0.0}
        ]

        # Clear any form-related session state
        form_keys = [
            key
            for key in st.session_state.keys()
            if key.startswith(("desc_", "qty_", "price_"))
        ]
        for key in form_keys:
            del st.session_state[key]

    def _add_notification(self, message: str, notification_type: str = "info") -> None:
        """Add notification to session state."""
        if "notification_queue" not in st.session_state:
            st.session_state.notification_queue = []

        notification = {
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now(),
            "id": f"{notification_type}_{len(st.session_state.notification_queue)}",
        }

        st.session_state.notification_queue.append(notification)

    def _render_line_item_management(self):
        """Render line item management buttons outside the form."""
        st.markdown("#### 📋 Manage Line Items")

        # Initialize line items if not exists
        if "line_items" not in st.session_state:
            st.session_state.line_items = [
                {"description": "", "quantity": 1, "unit_price": 0.0}
            ]

        col1, col2 = st.columns([1, 4])

        with col1:
            if st.button("➕ Add Item", key="add_item_btn"):
                st.session_state.line_items.append(
                    {"description": "", "quantity": 1, "unit_price": 0.0}
                )
                st.rerun()

        with col2:
            if len(st.session_state.line_items) > 1:
                # Show remove buttons for each item
                cols = st.columns(len(st.session_state.line_items))
                for i in range(len(st.session_state.line_items)):
                    with cols[i]:
                        if st.button(f"🗑️ Remove Item {i+1}", key=f"remove_item_{i}"):
                            st.session_state.line_items.pop(i)
                            st.rerun()
            else:
                st.info("At least one line item is required")
