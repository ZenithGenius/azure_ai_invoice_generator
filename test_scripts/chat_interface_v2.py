"""
Enhanced Invoice Management Chat Interface V3 - Modern Dashboard Edition
========================================================================

Modern web-based interface with improved navigation, better layout, and integrated analytics.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
from service_manager import get_service_manager
from invoice_document_generator import InvoiceDocumentGenerator
from analytics_dashboard import InvoiceAnalytics

# MUST be the first Streamlit command
st.set_page_config(
    page_title="🤖 Invoice Management AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/your-repo/invoice-management",
        "Report a bug": "https://github.com/your-repo/invoice-management/issues",
        "About": "# Invoice Management AI Assistant\nPowered by Azure AI Foundry & GPT-4o",
    },
)


class StreamlitInvoiceChatAgent:
    """Enhanced Streamlit-based chat agent with modern dashboard design."""

    def __init__(self):
        """Initialize the enhanced chat agent."""
        if "service_manager" not in st.session_state:
            with st.spinner("🔄 Initializing AI Assistant..."):
                st.session_state.service_manager = get_service_manager()
                st.session_state.doc_generator = InvoiceDocumentGenerator()
                st.session_state.analytics = InvoiceAnalytics()
                st.session_state.initialized = True

        self.service_manager = st.session_state.service_manager
        self.doc_generator = st.session_state.doc_generator
        self.analytics = st.session_state.analytics

        # Initialize session state variables
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables for enhanced UX."""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "👋 Hello! I'm your AI Invoice Assistant. I can help you generate invoices, search existing ones, analyze your business data, and much more!",
                    "timestamp": datetime.now(),
                }
            ]

        if "current_page" not in st.session_state:
            st.session_state.current_page = "Chat"

        if "current_invoice_data" not in st.session_state:
            st.session_state.current_invoice_data = {}

        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = datetime.now()

        if "auto_refresh" not in st.session_state:
            st.session_state.auto_refresh = False

        if "notification_queue" not in st.session_state:
            st.session_state.notification_queue = []

    def run(self):
        """Run the enhanced chat interface with navigation."""
        # Custom CSS for modern design
        self._inject_modern_css()

        # Navigation sidebar
        self._render_navigation_sidebar()

        # Main content area based on selected page
        if st.session_state.current_page == "Chat":
            self._render_chat_page()
        elif st.session_state.current_page == "Analytics":
            self._render_analytics_page()
        elif st.session_state.current_page == "Quick Invoice":
            self._render_quick_invoice_page()
        elif st.session_state.current_page == "System Status":
            self._render_system_status_page()

        # Handle real-time updates
        self._handle_real_time_updates()

    def _inject_modern_css(self):
        """Inject modern CSS for enhanced styling and fix contrast issues."""
        st.markdown(
            """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .main {
            font-family: 'Inter', sans-serif;
        }
        
        /* Fix white text on white background issues */
        .stMarkdown, .stText, p, span, div {
            color: #1f2937 !important;
        }
        
        /* Dark mode text fixes */
        @media (prefers-color-scheme: dark) {
            .stMarkdown, .stText, p, span, div {
                color: #f9fafb !important;
            }
        }
        
        /* Header Styles */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white !important;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .main-header h1 {
            color: white !important;
            margin: 0;
            font-weight: 700;
            font-size: 2.5rem;
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        
        /* Navigation Styles */
        .nav-container {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border: 1px solid #e5e7eb;
        }
        
        .nav-title {
            color: #1f2937 !important;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Card Styles */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        }
        
        .metric-card h3 {
            color: #1f2937 !important;
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .metric-card p {
            color: #6b7280 !important;
            margin: 0;
            font-size: 0.9rem;
        }
        
        /* Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .status-online {
            background-color: #d1fae5;
            color: #065f46 !important;
            border: 1px solid #10b981;
        }
        
        .status-warning {
            background-color: #fef3c7;
            color: #92400e !important;
            border: 1px solid #f59e0b;
        }
        
        .status-offline {
            background-color: #fee2e2;
            color: #991b1b !important;
            border: 1px solid #ef4444;
        }
        
        /* Chat Styles */
        .chat-container {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
            min-height: 500px;
        }
        
        .chat-message {
            padding: 1rem 1.5rem;
            margin: 1rem 0;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            position: relative;
        }
        
        .chat-user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            margin-left: 3rem;
            border-bottom-right-radius: 4px;
        }
        
        .chat-user * {
            color: white !important;
        }
        
        .chat-assistant {
            background: #f8fafc;
            color: #1f2937 !important;
            margin-right: 3rem;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        
        .chat-assistant * {
            color: #1f2937 !important;
        }
        
        .chat-timestamp {
            font-size: 0.8rem;
            opacity: 0.7;
            position: absolute;
            top: 0.5rem;
            right: 1rem;
        }
        
        /* Quick Actions */
        .quick-actions {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
        }
        
        .quick-actions h3 {
            color: #1f2937 !important;
            margin: 0 0 1rem 0;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        /* Button Styles */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Form Styles */
        .invoice-form {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
        }
        
        .invoice-form h3 {
            color: #1f2937 !important;
            margin: 0 0 1.5rem 0;
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        /* Notification Styles */
        .notification {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid;
            animation: slideIn 0.3s ease-out;
        }
        
        .notification-success {
            background-color: #d1fae5;
            border-left-color: #10b981;
            color: #065f46 !important;
        }
        
        .notification-error {
            background-color: #fee2e2;
            border-left-color: #ef4444;
            color: #991b1b !important;
        }
        
        .notification-info {
            background-color: #dbeafe;
            border-left-color: #3b82f6;
            color: #1e40af !important;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Analytics Styles */
        .analytics-container {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 2rem;
            }
            
            .chat-message {
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            
            .metric-card {
                margin-bottom: 1rem;
            }
        }
        
        /* Fix Streamlit default styles */
        .stSelectbox > div > div {
            background-color: white;
        }
        
        .stTextInput > div > div > input {
            background-color: white;
            color: #1f2937;
        }
        
        .stNumberInput > div > div > input {
            background-color: white;
            color: #1f2937;
        }
        
        .stTextArea > div > div > textarea {
            background-color: white;
            color: #1f2937;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_navigation_sidebar(self):
        """Render modern navigation sidebar."""
        with st.sidebar:
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
                "🔧 System Status": "System Status"
            }
            
            selected_page = st.radio(
                "Select Page",
                options=list(pages.keys()),
                index=list(pages.values()).index(st.session_state.current_page),
                label_visibility="collapsed"
            )
            
            st.session_state.current_page = pages[selected_page]
            
            st.markdown("---")
            
            # Quick Stats
            self._render_sidebar_stats()
            
            st.markdown("---")
            
            # System Controls
            self._render_system_controls()

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
                delta=f"+{stats.get('recent_invoices_30_days', 0)} this month"
            )
            
            # Outstanding Amount
            outstanding = stats.get("total_outstanding_amount", 0)
            st.metric(
                "Outstanding",
                f"${outstanding:,.2f}",
                delta="Needs attention" if outstanding > 10000 else "Good"
            )
            
            # Cache Performance
            cache_stats = self.service_manager.get_cache_statistics()
            hit_rate = cache_stats["performance"]["hit_rate_percent"]
            st.metric(
                "Cache Performance",
                f"{hit_rate:.1f}%",
                delta="Excellent" if hit_rate > 70 else "Good"
            )
            
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

    def _render_system_controls(self):
        """Render system control options."""
        st.markdown("### ⚙️ System Controls")
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.toggle(
            "Auto-refresh Data",
            value=st.session_state.auto_refresh,
            help="Automatically refresh data every 30 seconds"
        )
        
        # Manual refresh
        if st.button("🔄 Refresh Now", type="secondary"):
            self._force_refresh()
        
        # Last refresh time
        time_since_refresh = datetime.now() - st.session_state.last_refresh
        minutes_ago = int(time_since_refresh.total_seconds() / 60)
        if minutes_ago == 0:
            st.caption("🕒 Just updated")
        else:
            st.caption(f"🕒 Updated {minutes_ago}m ago")

    def _render_chat_page(self):
        """Render the main chat interface page."""
        # Header
        st.markdown(
            """
        <div class="main-header">
            <h1>💬 AI Chat Assistant</h1>
            <p>Ask me anything about your invoices, generate new ones, or get business insights!</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Display notifications
        self._display_notifications()

        # Quick Actions
        self._render_quick_actions()

        # Chat Interface
        self._render_chat_interface()

    def _render_analytics_page(self):
        """Render the analytics dashboard page."""
        # Header
        st.markdown(
            """
        <div class="main-header">
            <h1>📊 Analytics Dashboard</h1>
            <p>Comprehensive business intelligence and insights for your invoice management</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Render the analytics dashboard
        try:
            self.analytics.create_streamlit_dashboard()
        except Exception as e:
            st.error(f"Error loading analytics dashboard: {str(e)}")
            st.info("Please check your data connections and try again.")

    def _render_quick_invoice_page(self):
        """Render the quick invoice generation page."""
        # Header
        st.markdown(
            """
        <div class="main-header">
            <h1>📝 Quick Invoice Generator</h1>
            <p>Generate professional invoices quickly and easily</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Invoice form in main area
        self._render_invoice_form_full()

    def _render_system_status_page(self):
        """Render the system status page."""
        # Header
        st.markdown(
            """
        <div class="main-header">
            <h1>🔧 System Status</h1>
            <p>Monitor system health, performance, and service availability</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # System status details
        self._render_detailed_system_status()

    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.markdown(
            """
        <div class="quick-actions">
            <h3>⚡ Quick Actions</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 Show Statistics", key="quick_stats"):
                self._handle_quick_action("show statistics")

        with col2:
            if st.button("🔍 Search Invoices", key="quick_search"):
                self._handle_quick_action("search invoices")

        with col3:
            if st.button("📝 Generate Invoice", key="quick_generate"):
                self._handle_quick_action("generate new invoice")

        with col4:
            if st.button("📈 Open Analytics", key="quick_analytics"):
                st.session_state.current_page = "Analytics"
                st.rerun()

    def _render_chat_interface(self):
        """Render the chat interface."""
        st.markdown(
            """
        <div class="chat-container">
        """,
            unsafe_allow_html=True,
        )

        # Chat messages
        for message in st.session_state.messages:
            role_class = "chat-user" if message["role"] == "user" else "chat-assistant"
            icon = "👤" if message["role"] == "user" else "🤖"
            timestamp = message.get("timestamp", datetime.now()).strftime("%H:%M")

            st.markdown(
                f"""
            <div class="chat-message {role_class}">
                <div class="chat-timestamp">{timestamp}</div>
                <strong>{icon} {message["role"].title()}</strong>
                <br><br>
                {message["content"]}
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input(
            "Type your message here... (e.g., 'Generate an invoice for Acme Corp')"
        )

        if user_input:
            self._handle_user_input(user_input)

    def _render_invoice_form_full(self):
        """Render full invoice generation form."""
        st.markdown(
            """
        <div class="invoice-form">
            <h3>📝 Create New Invoice</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("full_invoice_form"):
            # Client Information Section
            st.markdown("#### 👤 Client Information")
            col1, col2 = st.columns(2)
            
            with col1:
                client_name = st.text_input(
                    "Client Name*", 
                    placeholder="e.g., Acme Corporation"
                )
                client_email = st.text_input(
                    "Client Email", 
                    placeholder="client@company.com"
                )
                
            with col2:
                client_address = st.text_area(
                    "Client Address",
                    placeholder="123 Business St, City, State, ZIP"
                )
                client_contact = st.text_input(
                    "Contact Person",
                    placeholder="John Smith, Manager"
                )

            st.markdown("---")
            
            # Invoice Details Section
            st.markdown("#### 📋 Invoice Details")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                po_number = st.text_input("PO Number", placeholder="Optional")
                payment_terms = st.selectbox(
                    "Payment Terms", 
                    ["Net 30", "Net 15", "Due on Receipt", "Net 60"]
                )
                
            with col2:
                currency = st.selectbox(
                    "Currency", 
                    ["USD", "EUR", "GBP", "FCFA"], 
                    index=3
                )
                tax_rate = st.number_input(
                    "Tax Rate (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=8.0, 
                    step=0.1
                )
                
            with col3:
                project_ref = st.text_input(
                    "Project Reference",
                    placeholder="Optional"
                )

            st.markdown("---")
            
            # Line Items Section
            st.markdown("#### 📦 Line Items")
            
            # Dynamic line items
            if "line_items" not in st.session_state:
                st.session_state.line_items = [{"description": "", "quantity": 1, "unit_price": 0.0}]
            
            for i, item in enumerate(st.session_state.line_items):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    description = st.text_input(
                        f"Description {i+1}*",
                        value=item["description"],
                        key=f"desc_{i}"
                    )
                    
                with col2:
                    quantity = st.number_input(
                        f"Qty {i+1}",
                        min_value=1,
                        value=item["quantity"],
                        key=f"qty_{i}"
                    )
                    
                with col3:
                    unit_price = st.number_input(
                        f"Unit Price {i+1}",
                        min_value=0.01,
                        value=item["unit_price"],
                        step=0.01,
                        key=f"price_{i}"
                    )
                    
                with col4:
                    total = quantity * unit_price
                    st.metric(f"Total {i+1}", f"${total:,.2f}")
            
            # Add/Remove item buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("➕ Add Item", type="secondary"):
                    st.session_state.line_items.append({"description": "", "quantity": 1, "unit_price": 0.0})
                    st.rerun()
                    
            with col2:
                if len(st.session_state.line_items) > 1:
                    if st.form_submit_button("➖ Remove Last", type="secondary"):
                        st.session_state.line_items.pop()
                        st.rerun()

            st.markdown("---")
            
            # Special Instructions
            notes = st.text_area(
                "Special Instructions",
                placeholder="Any special notes or instructions..."
            )

            # Generate button
            submitted = st.form_submit_button("🚀 Generate Invoice", type="primary")

            if submitted:
                if client_name and any(item["description"] for item in st.session_state.line_items):
                    # Prepare line items
                    items = []
                    for i, item in enumerate(st.session_state.line_items):
                        if st.session_state[f"desc_{i}"]:  # Only add items with descriptions
                            items.append({
                                "description": st.session_state[f"desc_{i}"],
                                "quantity": st.session_state[f"qty_{i}"],
                                "unit_price": st.session_state[f"price_{i}"]
                            })
                    
                    form_data = {
                        "client_name": client_name,
                        "client_email": client_email,
                        "client_address": client_address,
                        "client_contact": client_contact,
                        "items": items,
                        "tax_rate": tax_rate / 100,
                        "po_number": po_number,
                        "payment_terms": payment_terms,
                        "currency": currency,
                        "project_ref": project_ref,
                        "notes": notes,
                    }
                    
                    self._generate_quick_invoice(form_data)
                else:
                    st.error("Please fill in required fields (Client Name and at least one item description)")

    def _render_detailed_system_status(self):
        """Render detailed system status information."""
        # Service Status
        st.markdown("### 🔧 Service Status")
        
        status = self.service_manager.get_service_status_cached()
        services = status["services_available"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Core Services")
            for service_name, is_available in services.items():
                if service_name in ["ai_project", "cosmos"]:
                    status_class = "status-online" if is_available else "status-offline"
                    status_text = "Online" if is_available else "Offline"
                    icon = "🟢" if is_available else "🔴"
                    
                    st.markdown(
                        f"""
                    <div class="status-indicator {status_class}">
                        {icon} {service_name.replace('_', ' ').title()}: {status_text}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
        
        with col2:
            st.markdown("#### Storage & Search")
            for service_name, is_available in services.items():
                if service_name in ["blob_storage", "search"]:
                    status_class = "status-online" if is_available else "status-offline"
                    status_text = "Online" if is_available else "Offline"
                    icon = "🟢" if is_available else "🔴"
                    
                    st.markdown(
                        f"""
                    <div class="status-indicator {status_class}">
                        {icon} {service_name.replace('_', ' ').title()}: {status_text}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        
        # Performance Metrics
        st.markdown("### 📈 Performance Metrics")
        
        cache_stats = self.service_manager.get_cache_statistics()
        perf = cache_stats["performance"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cache Hit Rate", f"{perf['hit_rate_percent']:.1f}%")
        
        with col2:
            st.metric("Total Requests", f"{perf['total_requests']:,}")
        
        with col3:
            st.metric("Cache Hits", f"{perf['cache_hits']:,}")
        
        with col4:
            st.metric("Cache Misses", f"{perf['cache_misses']:,}")

        # Cache Details
        st.markdown("### 💾 Cache Details")
        
        cache_sizes = cache_stats["cache_sizes"]
        if cache_sizes:
            for cache_type, size in cache_sizes.items():
                if size > 0:
                    st.markdown(f"• **{cache_type.replace('_', ' ').title()}**: {size} items")

    def _generate_quick_invoice(self, form_data: Dict):
        """Generate invoice from form data."""
        try:
            # Prepare order details
            order_details = {
                "order_id": f"QUICK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "client_name": form_data["client_name"],
                "client_email": form_data.get("client_email", ""),
                "client_address": form_data.get("client_address", "Address to be provided"),
                "client_contact": form_data.get("client_contact", ""),
                "items": form_data["items"],
                "tax_rate": form_data["tax_rate"],
                "currency": form_data["currency"],
                "payment_terms": form_data["payment_terms"],
                "po_number": form_data.get("po_number", ""),
                "project_ref": form_data.get("project_ref", ""),
                "special_instructions": form_data.get("notes", ""),
            }

            # Generate invoice
            with st.spinner("🔄 Generating invoice..."):
                result = self.service_manager.generate_invoice(order_details)

            if result.get("success"):
                invoice_number = result["invoice_data"]["invoice_number"]
                self._add_notification(
                    f"✅ Invoice {invoice_number} generated successfully!", "success"
                )

                # Show success details
                st.success(f"🎉 Invoice {invoice_number} generated successfully!")
                
                # Display invoice summary
                total_amount = sum(item["quantity"] * item["unit_price"] for item in form_data["items"])
                tax_amount = total_amount * form_data["tax_rate"]
                final_total = total_amount + tax_amount
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Subtotal", f"${total_amount:,.2f}")
                with col2:
                    st.metric("Tax", f"${tax_amount:,.2f}")
                with col3:
                    st.metric("Total", f"${final_total:,.2f}")

                # Force refresh to update statistics
                self._force_refresh()

            else:
                error_msg = result.get("error", "Unknown error occurred")
                self._add_notification(
                    f"❌ Invoice generation failed: {error_msg}", "error"
                )

        except Exception as e:
            self._add_notification(f"❌ Error generating invoice: {str(e)}", "error")

    def _display_notifications(self):
        """Display notifications with improved styling."""
        if st.session_state.notification_queue:
            for notification in st.session_state.notification_queue:
                notification_type = notification.get("type", "info")
                message = notification.get("message", "")
                
                if notification_type == "success":
                    st.success(message)
                elif notification_type == "error":
                    st.error(message)
                elif notification_type == "warning":
                    st.warning(message)
                else:
                    st.info(message)
            
            # Clear notifications after display
            st.session_state.notification_queue = []

    def _handle_quick_action(self, action: str):
        """Handle quick action buttons."""
        # Add user message
        st.session_state.messages.append(
            {"role": "user", "content": action, "timestamp": datetime.now()}
        )

        # Process the action
        response = self._process_user_input(action)

        # Add assistant response
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "timestamp": datetime.now()}
        )

        # Rerun to update display
        st.rerun()

    def _handle_user_input(self, user_input: str):
        """Handle user input with enhanced processing."""
        # Add user message to chat
        st.session_state.messages.append(
            {"role": "user", "content": user_input, "timestamp": datetime.now()}
        )

        # Process input and get response
        with st.spinner("🤖 AI Assistant is thinking..."):
            response = self._process_user_input(user_input)

        # Add assistant response
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "timestamp": datetime.now()}
        )

        # Add success notification
        self._add_notification("Message processed successfully!", "success")

        # Rerun to update display
        st.rerun()

    def _process_user_input(self, user_input: str) -> str:
        """Process user input and return appropriate response."""
        user_input_lower = user_input.lower()

        try:
            # Enhanced command processing with better pattern matching
            if any(
                keyword in user_input_lower
                for keyword in ["statistics", "stats", "dashboard", "overview"]
            ):
                return self._generate_statistics_response()

            elif any(
                keyword in user_input_lower for keyword in ["search", "find", "lookup"]
            ):
                return self._handle_search_request(user_input)

            elif any(
                keyword in user_input_lower
                for keyword in ["generate", "create", "new invoice"]
            ):
                return self._handle_invoice_generation_request(user_input)

            elif any(
                keyword in user_input_lower
                for keyword in ["analytics", "analysis", "insights"]
            ):
                return self._generate_analytics_response()

            elif any(
                keyword in user_input_lower
                for keyword in ["help", "commands", "what can you do"]
            ):
                return self._generate_help_response()

            elif any(
                keyword in user_input_lower
                for keyword in ["status", "health", "system"]
            ):
                return self._generate_system_status_response()

            else:
                return self._generate_general_response(user_input)

        except Exception as e:
            self._add_notification(f"Error processing request: {str(e)}", "error")
            return f"❌ I encountered an error while processing your request: {str(e)}. Please try again or contact support."

    def _generate_statistics_response(self) -> str:
        """Generate enhanced statistics response."""
        stats = self.service_manager.get_statistics()

        total_invoices = stats.get("total_invoices", 0)
        outstanding_amount = stats.get("total_outstanding_amount", 0)
        recent_invoices = stats.get("recent_invoices_30_days", 0)
        avg_amount = stats.get("average_invoice_amount", 0)

        status_breakdown = stats.get("status_breakdown", [])
        status_summary = ", ".join(
            [f"{item['count']} {item['status']}" for item in status_breakdown]
        )

        response = f"""📊 **Business Statistics Dashboard**

**Key Metrics:**
• Total Invoices: **{total_invoices:,}**
• Outstanding Amount: **${outstanding_amount:,.2f}**
• Recent Invoices (30 days): **{recent_invoices}**
• Average Invoice Amount: **${avg_amount:,.2f}**

**Status Breakdown:** {status_summary}

**Insights:**
• Your business has processed {total_invoices} invoices to date
• You have ${outstanding_amount:,.2f} in outstanding payments
• Recent activity shows {recent_invoices} invoices in the last 30 days
• Your average invoice value is ${avg_amount:,.2f}

💡 **Tip:** Click the "📊 Open Analytics" button above or navigate to the Analytics Dashboard for detailed insights and visualizations!"""

        return response

    def _handle_search_request(self, user_input: str) -> str:
        """Handle search requests with enhanced functionality."""
        # Extract search terms from user input
        search_terms = (
            user_input.lower()
            .replace("search", "")
            .replace("find", "")
            .replace("lookup", "")
            .strip()
        )

        if not search_terms:
            return "🔍 Please specify what you'd like to search for. For example: 'search for Acme Corp invoices' or 'find invoices from December'."

        try:
            results = self.service_manager.search_invoices(search_terms)

            if not results:
                return f"🔍 No invoices found matching '{search_terms}'. Try different search terms or check the spelling."

            response = f"🔍 **Search Results for '{search_terms}'**\n\nFound {len(results)} matching invoices:\n\n"

            for i, invoice in enumerate(results[:5], 1):  # Show top 5 results
                invoice_num = invoice.get("invoice_number", "N/A")
                client_name = invoice.get("client", {}).get("name", "Unknown")
                total = invoice.get("total", 0)
                status = invoice.get("status", "unknown")
                date = invoice.get("invoice_date", "N/A")

                response += f"{i}. **{invoice_num}** - {client_name}\n"
                response += (
                    f"   Amount: ${total:,.2f} | Status: {status} | Date: {date}\n\n"
                )

            if len(results) > 5:
                response += f"... and {len(results) - 5} more results.\n\n"

            response += "Would you like me to show details for a specific invoice or perform another search?"

            return response

        except Exception as e:
            return f"❌ Search failed: {str(e)}. Please try again with different search terms."

    def _handle_invoice_generation_request(self, user_input: str) -> str:
        """Handle invoice generation requests."""
        return """📝 **Invoice Generation Assistant**

I can help you generate professional invoices! To create a new invoice, I'll need some information:

**Required Information:**
• Client name and address
• Items/services to invoice
• Quantities and prices
• Tax rate (if applicable)

**Example:** "Generate an invoice for Acme Corp for 10 hours of consulting at $150/hour"

**Easy Options:**
1. 📝 **Quick Invoice Page** - Use the navigation menu to access the full invoice form
2. 💬 **Tell me the details** - Describe your invoice in natural language here
3. 📋 **Use templates** - I can help you with common service templates

**Quick Access:** Click "📝 Quick Invoice" in the navigation menu for a guided experience!

What would you prefer?"""

    def _generate_analytics_response(self) -> str:
        """Generate analytics response with navigation tip."""
        stats = self.service_manager.get_statistics()

        total_invoices = stats.get("total_invoices", 0)
        outstanding_amount = stats.get("total_outstanding_amount", 0)
        recent_invoices = stats.get("recent_invoices_30_days", 0)
        avg_amount = stats.get("average_invoice_amount", 0)

        # Generate insights
        insights = []

        if outstanding_amount > 0:
            insights.append(
                f"💰 You have ${outstanding_amount:,.2f} in outstanding payments that need attention"
            )

        if recent_invoices > 0:
            monthly_projection = recent_invoices * avg_amount
            insights.append(
                f"📈 Based on recent activity, your monthly revenue projection is ${monthly_projection:,.2f}"
            )

        if avg_amount > 1000:
            insights.append(
                "💼 Your high average invoice value suggests premium service offerings"
            )

        response = f"""📈 **Business Analytics & Insights**

**Performance Overview:**
• Total Revenue Processed: ${total_invoices * avg_amount:,.2f}
• Outstanding Collections: ${outstanding_amount:,.2f}
• Recent Activity: {recent_invoices} invoices (30 days)
• Average Deal Size: ${avg_amount:,.2f}

**Key Insights:**
"""

        for insight in insights:
            response += f"• {insight}\n"

        if not insights:
            response += "• Your invoice data looks healthy! Keep up the good work.\n"

        response += """
**Recommendations:**
• Monitor outstanding payments regularly
• Consider automated payment reminders
• Track seasonal trends in your business
• Analyze client payment patterns

🚀 **Full Analytics Dashboard:** Use the navigation menu to access the complete Analytics Dashboard with interactive charts, forecasting, and detailed business intelligence!"""

        return response

    def _generate_help_response(self) -> str:
        """Generate comprehensive help response."""
        return """🤖 **AI Invoice Assistant - Help Guide**

**Navigation:**
• 💬 **Chat Assistant** - This page! Ask questions and get help
• 📊 **Analytics Dashboard** - Complete business intelligence with charts
• 📝 **Quick Invoice** - Generate invoices with guided forms
• 🔧 **System Status** - Monitor system health and performance

**What I Can Do:**
• 📝 Generate professional invoices
• 🔍 Search and find existing invoices
• 📊 Provide business statistics and analytics
• 💰 Track outstanding payments
• 📈 Generate insights and reports
• 🏥 Monitor system health

**Quick Commands:**
• "Show statistics" - Display business overview
• "Search for [client name]" - Find specific invoices
• "Generate invoice for [client]" - Create new invoice
• "Show analytics" - Business insights
• "System status" - Check service health

**Examples:**
• "Generate an invoice for Acme Corp for $5,000"
• "Search for invoices from December"
• "Show me outstanding payments"
• "What's my total revenue this month?"

**Tips:**
• Use natural language - I understand context!
• Be specific with search terms for better results
• Use the navigation menu to access different features
• Check the Analytics Dashboard for detailed insights

Need help with something specific? Just ask! 😊"""

    def _generate_system_status_response(self) -> str:
        """Generate system status response."""
        status = self.service_manager.get_service_status_cached()
        services = status["services_available"]
        cache_stats = status.get("cache_statistics", {})

        # Service status
        online_services = sum(services.values())
        total_services = len(services)

        response = f"""🏥 **System Health Status**

**Service Status:** {online_services}/{total_services} services online

"""

        for service_name, is_available in services.items():
            status_icon = "🟢" if is_available else "🔴"
            status_text = "Online" if is_available else "Offline"
            response += f"• {status_icon} **{service_name.title()}**: {status_text}\n"

        # Cache performance
        if cache_stats:
            performance = cache_stats.get("performance", {})
            hit_rate = performance.get("hit_rate_percent", 0)
            total_requests = performance.get("total_requests", 0)

            response += f"""
**Performance Metrics:**
• Cache Hit Rate: {hit_rate:.1f}%
• Total Requests: {total_requests:,}
• System Response: Optimal

**Status:** {"🟢 All systems operational" if online_services == total_services else "⚠️ Some services need attention"}

💡 **Tip:** Visit the System Status page in the navigation menu for detailed performance metrics and monitoring!"""

        return response

    def _generate_general_response(self, user_input: str) -> str:
        """Generate general response for unrecognized input."""
        return f"""🤖 I understand you said: "{user_input}"

I'm here to help with invoice management! Here are some things I can assist you with:

• 📝 **Generate Invoices** - Create professional invoices
• 🔍 **Search & Find** - Locate existing invoices
• 📊 **Business Analytics** - View statistics and insights
• 💰 **Payment Tracking** - Monitor outstanding amounts

**Navigation Options:**
• Use the sidebar menu to access different features
• 📊 Analytics Dashboard for detailed insights
• 📝 Quick Invoice for guided invoice creation
• 🔧 System Status for performance monitoring

**Try asking:**
• "Show me my business statistics"
• "Search for invoices from [client name]"
• "Generate an invoice for [client]"
• "What's my outstanding balance?"

Or use the quick action buttons above for common tasks! How can I help you today?"""

    def _add_notification(self, message: str, notification_type: str = "info"):
        """Add notification to queue."""
        st.session_state.notification_queue.append(
            {"message": message, "type": notification_type, "timestamp": datetime.now()}
        )

    def _force_refresh(self):
        """Force refresh of all data."""
        # Clear caches
        self.service_manager._clear_cache()

        # Update timestamp
        st.session_state.last_refresh = datetime.now()

        # Add notification
        self._add_notification("Data refreshed successfully!", "success")

        # Rerun to update display
        st.rerun()

    def _handle_real_time_updates(self):
        """Handle real-time updates with configurable intervals."""
        if st.session_state.auto_refresh:
            # Check if 30 seconds have passed since last refresh
            time_since_refresh = datetime.now() - st.session_state.last_refresh

            if time_since_refresh.total_seconds() > 30:
                # Auto-refresh data
                st.session_state.last_refresh = datetime.now()

                # Add subtle notification
                self._add_notification("🔄 Data auto-refreshed", "info")

                # Rerun to update display
                st.rerun()


def main():
    """Main function to run the enhanced Streamlit app."""
    try:
        # Initialize and run the enhanced chat agent
        agent = StreamlitInvoiceChatAgent()
        agent.run()

    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please refresh the page or contact support if the problem persists.")

        # Show error details in expander for debugging
        with st.expander("🔧 Technical Details"):
            st.code(str(e))


if __name__ == "__main__":
    main()
