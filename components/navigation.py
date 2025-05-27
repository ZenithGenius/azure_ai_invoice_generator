"""
Navigation Component for Invoice Management Dashboard
===================================================

Handles sidebar navigation and page routing.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any


class NavigationComponent:
    """Handles navigation and sidebar functionality."""

    def __init__(self, service_manager):
        """Initialize navigation component."""
        self.service_manager = service_manager

    def render_sidebar(self) -> str:
        """Render the navigation sidebar and return selected page."""
        with st.sidebar:
            # Header
            st.markdown(
                """
                <div class="nav-container">
                    <div class="nav-title">🤖 Invoice AI Assistant</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Navigation Menu
            st.markdown("### 📋 Navigation")

            # Page selection
            pages = {
                "💬 Chat Assistant": "Chat",
                "📊 Analytics Dashboard": "Analytics",
                "📝 Quick Invoice": "Quick Invoice",
                "🔧 System Status": "System Status",
            }

            current_page = st.session_state.get("current_page", "Chat")
            selected_page = st.radio(
                "Select Page",
                options=list(pages.keys()),
                index=list(pages.values()).index(current_page),
                label_visibility="collapsed",
            )

            # Update session state
            st.session_state.current_page = pages[selected_page]

            st.markdown("---")

            # AI Shortcut Buttons
            self._render_ai_shortcuts()

            st.markdown("---")

            # Download Center
            self._render_download_center()

            st.markdown("---")

            # Quick Stats
            self._render_sidebar_stats()

            st.markdown("---")

            # System Controls
            self._render_system_controls()

            return pages[selected_page]

    def _render_ai_shortcuts(self):
        """Render AI shortcut buttons in sidebar."""
        st.markdown("### 🤖 AI Shortcuts")

        # Quick AI actions
        if st.button("📊 Show Statistics", key="ai_stats", use_container_width=True):
            self._handle_ai_shortcut("show me my business statistics")

        if st.button(
            "🔍 Find Recent Invoices", key="ai_recent", use_container_width=True
        ):
            self._handle_ai_shortcut("show me recent invoices from the last 30 days")

        if st.button(
            "💰 Outstanding Balance", key="ai_balance", use_container_width=True
        ):
            self._handle_ai_shortcut("what's my total outstanding balance?")

        if st.button(
            "📈 Business Insights", key="ai_insights", use_container_width=True
        ):
            self._handle_ai_shortcut("give me insights about my business performance")

        if st.button("🔧 System Health", key="ai_health", use_container_width=True):
            self._handle_ai_shortcut("check my system status and performance")

        # Test Analytics Chat button
        if st.button(
            "🧪 Test Analytics Chat",
            key="test_analytics_chat_sidebar",
            use_container_width=True,
        ):
            self._handle_test_analytics_chat()

        # Invoice Gallery button
        if st.button("📁 Invoice Gallery", key="gallery_sidebar", use_container_width=True):
            self._handle_invoice_gallery()

    def _render_download_center(self):
        """Render download center with various export options."""
        st.markdown("### 📥 Download Center")

        # Invoice Downloads
        st.markdown("**📄 Invoices**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "📋 Invoice List", key="download_invoice_list", use_container_width=True
            ):
                self._download_invoice_list()

        with col2:
            if st.button(
                "📊 Invoice Report",
                key="download_invoice_report",
                use_container_width=True,
            ):
                self._download_invoice_report()

        # Analytics Downloads
        st.markdown("**📈 Analytics**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "📊 Statistics CSV", key="download_stats_csv", use_container_width=True
            ):
                self._download_statistics_csv()

        with col2:
            if st.button(
                "📈 Analytics PDF",
                key="download_analytics_pdf",
                use_container_width=True,
            ):
                self._download_analytics_pdf()

        # System Reports
        st.markdown("**🔧 System**")
        if st.button(
            "🔍 System Report", key="download_system_report", use_container_width=True
        ):
            self._download_system_report()

    def _handle_ai_shortcut(self, query: str):
        """Handle AI shortcut button clicks."""
        # Add the query to chat messages
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Add user message
        st.session_state.messages.append(
            {"role": "user", "content": query, "timestamp": datetime.now()}
        )

        # Switch to chat page
        st.session_state.current_page = "Chat"

        # Clear any existing processing flags to ensure fresh processing
        if hasattr(st.session_state, "processing_message"):
            del st.session_state.processing_message

        # Add notification
        if "notification_queue" not in st.session_state:
            st.session_state.notification_queue = []
        st.session_state.notification_queue.append(
            {
                "message": f"🤖 Processing AI query: {query[:50]}...",
                "type": "info",
                "timestamp": datetime.now(),
            }
        )

        # Rerun to process the query
        st.rerun()

    def _handle_test_analytics_chat(self):
        """Handle test analytics chat functionality."""
        try:
            # Add a test message to chat
            if "messages" not in st.session_state:
                st.session_state.messages = []

            test_message = (
                "Test message from analytics - show me my business performance"
            )

            # Add user message
            st.session_state.messages.append(
                {"role": "user", "content": test_message, "timestamp": datetime.now()}
            )

            # Switch to chat page
            st.session_state.current_page = "Chat"

            # Clear any existing processing flags
            if hasattr(st.session_state, "processing_message"):
                del st.session_state.processing_message

            # Add notification
            if "notification_queue" not in st.session_state:
                st.session_state.notification_queue = []
            st.session_state.notification_queue.append(
                {
                    "message": "🧪 Analytics Chat Test Activated! Processing test query...",
                    "type": "info",
                    "timestamp": datetime.now(),
                }
            )

            st.rerun()

        except Exception as e:
            st.error(f"Error activating test analytics chat: {e}")

    def _handle_invoice_gallery(self):
        """Handle invoice gallery functionality."""
        try:
            # Switch to chat page first
            st.session_state.current_page = "Chat"
            
            # Activate invoice gallery
            st.session_state.show_invoice_gallery = True
            
            # Add notification
            if "notification_queue" not in st.session_state:
                st.session_state.notification_queue = []
            st.session_state.notification_queue.append(
                {
                    "message": "📁 Invoice Gallery opened! Browse your generated invoices.",
                    "type": "info",
                    "timestamp": datetime.now(),
                }
            )
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error opening invoice gallery: {e}")

    def _download_invoice_list(self):
        """Download invoice list as CSV."""
        try:
            import pandas as pd
            import io

            # Get invoice data
            invoices = self.service_manager.list_invoices(limit=1000)

            if not invoices:
                st.warning("No invoices found to download.")
                return

            # Prepare data for CSV
            csv_data = []
            for invoice in invoices:
                invoice_data = invoice.get("invoice_data", invoice)
                client = invoice_data.get("client", {})

                csv_data.append(
                    {
                        "Invoice Number": invoice_data.get("invoice_number", ""),
                        "Date": invoice_data.get("invoice_date", ""),
                        "Client Name": client.get("name", ""),
                        "Client Email": client.get("email", ""),
                        "Total": invoice_data.get("total", 0),
                        "Currency": invoice_data.get("currency", "USD"),
                        "Status": invoice_data.get("status", ""),
                        "Payment Terms": invoice_data.get("payment_terms", ""),
                        "PO Number": invoice_data.get("po_number", ""),
                    }
                )

            # Create DataFrame and CSV
            df = pd.DataFrame(csv_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)

            # Provide download
            st.download_button(
                label="📥 Download Invoice List CSV",
                data=csv_buffer.getvalue(),
                file_name=f"invoice_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv_btn",
            )

            st.success(
                f"✅ Invoice list prepared! {len(csv_data)} invoices ready for download."
            )

        except Exception as e:
            st.error(f"❌ Error preparing invoice list: {str(e)}")

    def _download_invoice_report(self):
        """Download detailed invoice report as HTML."""
        try:
            # Get invoice data and statistics
            invoices = self.service_manager.list_invoices(limit=100)
            stats = self.service_manager.get_statistics()

            # Generate HTML report
            html_content = self._generate_invoice_report_html(invoices, stats)

            # Provide download
            st.download_button(
                label="📥 Download Invoice Report HTML",
                data=html_content,
                file_name=f"invoice_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                key="download_report_btn",
            )

            st.success("✅ Invoice report prepared for download!")

        except Exception as e:
            st.error(f"❌ Error preparing invoice report: {str(e)}")

    def _download_statistics_csv(self):
        """Download business statistics as CSV."""
        try:
            import pandas as pd
            import io

            # Get statistics
            stats = self.service_manager.get_statistics()
            cache_stats = self.service_manager.get_cache_statistics()

            # Prepare statistics data
            stats_data = [
                {"Metric": "Total Invoices", "Value": stats.get("total_invoices", 0)},
                {
                    "Metric": "Outstanding Amount",
                    "Value": stats.get("total_outstanding_amount", 0),
                },
                {
                    "Metric": "Average Invoice Amount",
                    "Value": stats.get("average_invoice_amount", 0),
                },
                {
                    "Metric": "Recent Invoices (30 days)",
                    "Value": stats.get("recent_invoices_30_days", 0),
                },
                {
                    "Metric": "Cache Hit Rate (%)",
                    "Value": cache_stats["performance"]["hit_rate_percent"],
                },
                {
                    "Metric": "Total Cache Requests",
                    "Value": cache_stats["performance"]["total_requests"],
                },
                {
                    "Metric": "System Timestamp",
                    "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            ]

            # Create DataFrame and CSV
            df = pd.DataFrame(stats_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)

            # Provide download
            st.download_button(
                label="📥 Download Statistics CSV",
                data=csv_buffer.getvalue(),
                file_name=f"business_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_stats_csv_btn",
            )

            st.success("✅ Statistics CSV prepared for download!")

        except Exception as e:
            st.error(f"❌ Error preparing statistics: {str(e)}")

    def _download_analytics_pdf(self):
        """Download analytics report as PDF (placeholder - would need PDF generation)."""
        st.info(
            "📄 PDF analytics report generation coming soon! For now, use the HTML report option."
        )

    def _download_system_report(self):
        """Download system status report."""
        try:
            # Get system status
            status = self.service_manager.get_service_status()
            cache_stats = self.service_manager.get_cache_statistics()

            # Generate system report
            report_content = self._generate_system_report_text(status, cache_stats)

            # Provide download
            st.download_button(
                label="📥 Download System Report",
                data=report_content,
                file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_system_btn",
            )

            st.success("✅ System report prepared for download!")

        except Exception as e:
            st.error(f"❌ Error preparing system report: {str(e)}")

    def _generate_invoice_report_html(self, invoices, stats):
        """Generate HTML invoice report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Invoice Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #e8f4fd; padding: 15px; border-radius: 5px; flex: 1; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Invoice Management Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Total Invoices</h3>
            <p>{stats.get('total_invoices', 0)}</p>
        </div>
        <div class="stat-card">
            <h3>Outstanding Amount</h3>
            <p>${stats.get('total_outstanding_amount', 0):,.2f}</p>
        </div>
        <div class="stat-card">
            <h3>Average Invoice</h3>
            <p>${stats.get('average_invoice_amount', 0):,.2f}</p>
        </div>
    </div>
    
    <h2>📋 Recent Invoices</h2>
    <table>
        <tr>
            <th>Invoice Number</th>
            <th>Client</th>
            <th>Date</th>
            <th>Amount</th>
            <th>Status</th>
        </tr>
"""

        for invoice in invoices[:50]:  # Limit to 50 for report
            invoice_data = invoice.get("invoice_data", invoice)
            client = invoice_data.get("client", {})
            html += f"""
        <tr>
            <td>{invoice_data.get('invoice_number', 'N/A')}</td>
            <td>{client.get('name', 'N/A')}</td>
            <td>{invoice_data.get('invoice_date', 'N/A')}</td>
            <td>${invoice_data.get('total', 0):,.2f}</td>
            <td>{invoice_data.get('status', 'N/A')}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""
        return html

    def _generate_system_report_text(self, status, cache_stats):
        """Generate system status report as text."""
        report = f"""
SYSTEM STATUS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

SERVICE STATUS:
"""

        services = status.get("services_available", {})
        for service, available in services.items():
            status_text = "✅ ONLINE" if available else "❌ OFFLINE"
            report += f"  {service.upper()}: {status_text}\n"

        report += f"""
CACHE PERFORMANCE:
  Total Requests: {cache_stats['performance']['total_requests']:,}
  Cache Hits: {cache_stats['performance']['cache_hits']:,}
  Cache Misses: {cache_stats['performance']['cache_misses']:,}
  Hit Rate: {cache_stats['performance']['hit_rate_percent']:.1f}%
  
CACHE SIZES:
"""

        for cache_type, size in cache_stats.get("cache_sizes", {}).items():
            report += f"  {cache_type}: {size} items\n"

        report += f"""
MEMORY USAGE:
  Total Cached Items: {cache_stats['total_cached_items']}
  Cache Entries: {cache_stats['memory_usage']['cache_entries']}
  Timestamp Entries: {cache_stats['memory_usage']['timestamp_entries']}
  
END OF REPORT
"""
        return report

    def _render_sidebar_stats(self):
        """Render quick statistics in sidebar."""
        st.markdown("### 📈 Quick Stats")

        try:
            stats = self.service_manager.get_statistics()

            # Total Invoices
            total_invoices = stats.get("total_invoices", 0)
            st.metric(
                "Total Invoices",
                total_invoices,
                delta=f"+{stats.get('recent_invoices_30_days', 0)} this month",
            )

            # Outstanding Amount
            outstanding = stats.get("total_outstanding_amount", 0)
            st.metric(
                "Outstanding",
                f"${outstanding:,.2f}",
                delta="Needs attention" if outstanding > 10000 else "Good",
            )

            # Cache Performance
            cache_stats = self.service_manager.get_cache_statistics()
            hit_rate = cache_stats["performance"]["hit_rate_percent"]
            st.metric(
                "Cache Performance",
                f"{hit_rate:.1f}%",
                delta="Excellent" if hit_rate > 70 else "Good",
            )

        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

    def _render_system_controls(self):
        """Render system control options."""
        st.markdown("### ⚙️ System Controls")

        # Auto-refresh toggle
        st.session_state.auto_refresh = st.toggle(
            "Auto-refresh Data",
            value=st.session_state.get("auto_refresh", False),
            help="Automatically refresh data every 30 seconds",
            key="nav_auto_refresh",
        )

        # Manual refresh
        if st.button("🔄 Refresh Now", type="secondary", key="nav_refresh_btn"):
            self._force_refresh()

        # Last refresh time
        last_refresh = st.session_state.get("last_refresh", datetime.now())
        time_since_refresh = datetime.now() - last_refresh
        minutes_ago = int(time_since_refresh.total_seconds() / 60)
        if minutes_ago == 0:
            st.caption("🕒 Just updated")
        else:
            st.caption(f"🕒 Updated {minutes_ago}m ago")

    def _force_refresh(self):
        """Force refresh of all data."""
        # Clear caches
        self.service_manager._clear_cache()

        # Update timestamp
        st.session_state.last_refresh = datetime.now()

        # Add notification
        if "notification_queue" not in st.session_state:
            st.session_state.notification_queue = []
        st.session_state.notification_queue.append(
            {
                "message": "Data refreshed successfully!",
                "type": "success",
                "timestamp": datetime.now(),
            }
        )

        # Rerun to update display
        st.rerun()
 