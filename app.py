"""
Modern Invoice Management Dashboard - Modular Architecture
=========================================================

A clean, modular Streamlit application for invoice management with improved UI/UX.
"""

import streamlit as st
from datetime import datetime

# Import components
from components.navigation import NavigationComponent
from components.invoice_form import InvoiceFormComponent
from components.ai_chat import AIConversationComponent
from components.invoice_gallery import InvoiceGalleryComponent

# Import services
from service_manager import get_service_manager
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


class ModernInvoiceApp:
    """Modern, modular invoice management application."""

    def __init__(self):
        """Initialize the application."""
        self._initialize_services()
        self._initialize_components()
        self._initialize_session_state()

    def _initialize_services(self):
        """Initialize backend services."""
        if "service_manager" not in st.session_state:
            with st.spinner("🔄 Initializing AI Assistant..."):
                st.session_state.service_manager = get_service_manager()
                st.session_state.analytics = InvoiceAnalytics()
                st.session_state.initialized = True

        self.service_manager = st.session_state.service_manager
        self.analytics = st.session_state.analytics

    def _initialize_components(self):
        """Initialize UI components."""
        self.navigation = NavigationComponent(self.service_manager)
        self.invoice_form = InvoiceFormComponent(self.service_manager)
        self.ai_chat = AIConversationComponent(self.service_manager)
        self.invoice_gallery = InvoiceGalleryComponent()

    def _initialize_session_state(self):
        """Initialize session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": """👋 **Hello! I'm your AI Invoice Assistant!** 

I'm here to help you manage your invoices and business data with natural conversation. You can ask me anything like:

• *"Show me my business statistics"* 📊
• *"Find invoices for [client name]"* 🔍  
• *"Help me create a new invoice"* 📝
• *"What's my outstanding balance?"* 💰
• *"How is my business performing?"* 📈

I have access to your real business data and can provide specific insights, search results, and guidance. Just ask me naturally - no need for specific commands!

**What would you like to know about your business today?** 😊""",
                    "timestamp": datetime.now(),
                }
            ]

        if "current_page" not in st.session_state:
            st.session_state.current_page = "Chat"

        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = datetime.now()

        if "auto_refresh" not in st.session_state:
            st.session_state.auto_refresh = False

        if "notification_queue" not in st.session_state:
            st.session_state.notification_queue = []

        # Invoice gallery state
        if "show_invoice_gallery" not in st.session_state:
            st.session_state.show_invoice_gallery = False

    def run(self):
        """Run the application."""
        # Inject modern CSS
        self._inject_modern_css()

        # Render navigation and get current page
        current_page = self.navigation.render_sidebar()

        # Render main content based on selected page
        if current_page == "Chat":
            self._render_chat_page()
        elif current_page == "Analytics":
            self._render_analytics_page()
        elif current_page == "Quick Invoice":
            self._render_quick_invoice_page()
        elif current_page == "System Status":
            self._render_system_status_page()

        # Handle real-time updates
        self._handle_real_time_updates()

    def _inject_modern_css(self):
        """Inject modern CSS for enhanced styling."""
        st.markdown(
            """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .main {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
        }
        
        /* Fix text contrast issues */
        .stMarkdown, .stText, p, span, div {
            color: #1f2937 !important;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .main {
                background-color: #0f172a;
            }
            .stMarkdown, .stText, p, span, div {
                color: #f1f5f9 !important;
            }
        }
        
        /* Header Styles */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem 2rem;
            border-radius: 16px;
            color: white !important;
            margin-bottom: 2rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            text-align: center;
        }
        
        .main-header h1 {
            color: white !important;
            margin: 0;
            font-weight: 700;
            font-size: 2.5rem;
            line-height: 1.2;
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 1rem 0 0 0;
            font-size: 1.125rem;
            font-weight: 400;
        }
        
        /* Navigation Styles */
        .nav-container {
            background: #1976F0FF;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #1976F0FF;
        }
        
        .nav-title {
            color: white !important;
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Content Container */
        .content-container {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #e2e8f0;
            min-height: auto;
        }
        
        /* Chat-specific container with minimal padding */
        .chat-content-container {
            background: white;
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #667eea;
        }
        
        /* Card Styles */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            border: 1px solid #e2e8f0;
            margin-bottom: 1rem;
            transition: all 0.2s ease-in-out;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-online {
            background-color: #dcfce7;
            color: #166534 !important;
            border: 1px solid #22c55e;
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
            max-height: 60vh;
            overflow-y: auto;
            padding: 1rem 0;
        }
        
        .chat-message {
            padding: 1.25rem 1.5rem;
            margin: 1rem 0;
            border-radius: 12px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            position: relative;
            max-width: 85%;
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
            background: #667eea;
            color: white !important;
            margin-right: 3rem;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        
        .chat-assistant * {
            color: white !important;
        }
        
        /* Quick Actions */
        .quick-actions {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }
        
        .quick-actions h3 {
            color: #1e293b !important;
            margin: 0 0 1rem 0;
            font-size: 1.25rem;
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
            transition: all 0.2s ease-in-out;
            width: 100%;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Form Styles */
        .invoice-form {
            background: #161b22;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            border: 1px solid #30363d;
        }
        
        .invoice-form h3 {
            color: #ffffff !important;
            margin: 0 0 1.5rem 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        /* Input Styles */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div {
            background-color: white !important;
            color: #1e293b !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        /* Dark Mode Input Styles for Quick Invoice Page */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 2px solid #404040 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            transition: all 0.3s ease-in-out !important;
            font-family: 'Inter', monospace !important;
            font-size: 14px !important;
            caret-color: #00ff00 !important; /* Green blinking cursor */
        }
        
        /* Dark Mode Focus States */
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stNumberInput > div > div > input:focus {
            background-color: #0d1117 !important;
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3) !important;
            color: #ffffff !important;
            outline: none !important;
        }
        
        /* Dark Mode Placeholder Text */
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: #8b949e !important;
            opacity: 0.8 !important;
        }
        
        /* Dark Mode Selectbox */
        .stSelectbox > div > div {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 2px solid #404040 !important;
            border-radius: 8px !important;
        }
        
        /* Dark Mode Labels */
        .stTextInput > label,
        .stTextArea > label,
        .stNumberInput > label,
        .stSelectbox > label {
            color: #ffffff !important;
            font-weight: 500 !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Dark Mode Section Headers */
        .stMarkdown h4 {
            color: #ffffff !important;
            border-bottom: 1px solid #30363d !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* Dark Mode Metrics */
        .stMetric {
            background-color: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }
        
        .stMetric > div {
            color: #ffffff !important;
        }
        
        /* Auto-focus for first input */
        .stTextInput:first-of-type input {
            animation: blink-caret 1s step-end infinite;
        }
        
        @keyframes blink-caret {
            from, to { border-right-color: transparent; }
            50% { border-right-color: #00ff00; }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 2rem;
            }
            
            .chat-message {
                margin-left: 0 !important;
                margin-right: 0 !important;
                max-width: 100% !important;
            }
            
            .content-container {
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            .chat-container {
                max-height: 60vh;
            }
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        
        /* Remove Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_chat_page(self):
        """Render the chat interface page."""
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

        # Check for unprocessed user messages (from AI shortcuts)
        self._process_pending_messages()

        # Quick Actions
        self._render_quick_actions()

        # Chat Interface
        self._render_chat_interface()

    def _process_pending_messages(self):
        """Process any pending user messages that haven't received AI responses."""
        if not st.session_state.messages:
            return

        # Check if the last message is from user and doesn't have a response
        if (
            len(st.session_state.messages) > 0
            and st.session_state.messages[-1]["role"] == "user"
        ):
            # Check if this is a new message that needs processing
            last_message = st.session_state.messages[-1]

            # Add a flag to track if we're processing to avoid infinite loops
            if not hasattr(st.session_state, "processing_message"):
                st.session_state.processing_message = True

                try:
                    # Process the last user message
                    user_input = last_message["content"]

                    with st.spinner("🤖 AI Assistant is thinking..."):
                        response = self._process_user_input(user_input)

                    # Add assistant response
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.now(),
                        }
                    )

                    # Add success notification
                    if "notification_queue" not in st.session_state:
                        st.session_state.notification_queue = []
                    st.session_state.notification_queue.append(
                        {
                            "message": "✅ AI response generated successfully!",
                            "type": "success",
                            "timestamp": datetime.now(),
                        }
                    )

                except Exception as e:
                    # Add error message if processing fails
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"❌ I encountered an error processing your request: {str(e)}. Please try again.",
                            "timestamp": datetime.now(),
                        }
                    )

                    # Add error notification
                    if "notification_queue" not in st.session_state:
                        st.session_state.notification_queue = []
                    st.session_state.notification_queue.append(
                        {
                            "message": f"❌ Error processing AI query: {str(e)}",
                            "type": "error",
                            "timestamp": datetime.now(),
                        }
                    )

                finally:
                    # Always clear the processing flag
                    if hasattr(st.session_state, "processing_message"):
                        del st.session_state.processing_message

                    # Rerun to update display
                    st.rerun()

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

        # Render analytics in content container
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        try:
            self.analytics.create_streamlit_dashboard()
        except Exception as e:
            st.error(f"Error loading analytics dashboard: {str(e)}")
            st.info("Please check your data connections and try again.")
            # Show a basic fallback message
            st.markdown("### 📊 Analytics Dashboard Unavailable")
            st.markdown(
                "The analytics dashboard is currently unavailable. You can still use the AI chat below to ask questions about your business."
            )
        finally:
            # Always close the content container
            st.markdown("</div>", unsafe_allow_html=True)

        # Add chat functionality to analytics page (always render this)
        try:
            st.markdown("---")
            st.markdown("### 💬 Ask AI About Your Analytics")

            # Display recent chat messages (last 3 for analytics page)
            recent_messages = (
                st.session_state.messages[-3:]
                if len(st.session_state.messages) > 1
                else []
            )

            if recent_messages:
                st.markdown("#### Recent Conversation:")
                for message in recent_messages:
                    if message["role"] == "user":
                        st.markdown(f"**👤 You:** {message['content']}")
                    else:
                        st.markdown(f"**🤖 AI Assistant:** {message['content']}")
                    st.markdown("---")
            else:
                st.markdown(
                    "*No recent conversation. Start by asking a question below!*"
                )

            # Chat input for analytics page
            analytics_input = st.chat_input(
                "Ask me about your analytics... (e.g., 'Explain my revenue trends' or 'What should I focus on?')",
                key="analytics_chat_input",
            )

            # Debug: Show if input was detected
            if analytics_input:
                st.write(f"🔍 Debug: Received input: {analytics_input}")
                self._handle_analytics_chat(analytics_input)

        except Exception as e:
            st.error(f"Error in analytics chat: {str(e)}")
            st.info("Chat functionality is temporarily unavailable.")

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

        # Display notifications
        self._display_notifications()

        # Invoice form
        self.invoice_form.render_quick_invoice_form()

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

        # System status in content container
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        self._render_detailed_system_status()
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_quick_actions(self):
        """Render quick action buttons."""

        col1, col2, col3, col4, col5 = st.columns(5)

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
            if st.button("📁 View Invoices", key="quick_gallery"):
                st.session_state.show_invoice_gallery = True
                st.rerun()

        with col5:
            if st.button("📈 Open Analytics", key="quick_analytics"):
                st.session_state.current_page = "Analytics"
                st.rerun()

    def _render_chat_interface(self):
        """Render the chat interface."""
        # Show Invoice Gallery if active
        if st.session_state.get("show_invoice_gallery", False):
            st.markdown("---")

            # Gallery header with close button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("## 📁 Invoice Gallery")
            with col2:
                if st.button("❌ Close Gallery", key="close_gallery"):
                    st.session_state.show_invoice_gallery = False
                    st.rerun()

            # Render the gallery
            self.invoice_gallery.render_invoice_gallery()
            st.markdown("---")
            return  # Don't show chat when gallery is open

        # Chat messages container (no white container wrapper)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Chat messages
        for i, message in enumerate(st.session_state.messages):
            role_class = "chat-user" if message["role"] == "user" else "chat-assistant"
            icon = "👤" if message["role"] == "user" else "🤖"
            timestamp = message.get("timestamp", datetime.now()).strftime("%H:%M")

            st.markdown(
                f"""
            <div class="chat-message {role_class}">
                <div style="font-size: 0.8rem; opacity: 0.5; float: right;">{timestamp}</div>
                <strong>{icon} {message["role"].title()}</strong>
                <br><br>
                {message["content"]}
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show suggested follow-up questions for the last assistant message
            if (
                message["role"] == "assistant"
                and i == len(st.session_state.messages) - 1
                and len(st.session_state.messages) > 1
            ):
                user_message = (
                    st.session_state.messages[i - 1]["content"] if i > 0 else ""
                )
                suggestions = self.ai_chat.suggest_follow_up_questions(
                    user_message, message["content"]
                )

                if suggestions:
                    st.markdown("**💡 Suggested questions:**")
                    cols = st.columns(len(suggestions))
                    for j, suggestion in enumerate(suggestions):
                        with cols[j]:
                            if st.button(
                                f"💬 {suggestion}",
                                key=f"suggestion_{i}_{j}",
                                type="secondary",
                            ):
                                self._handle_user_input(suggestion)

        st.markdown("</div>", unsafe_allow_html=True)  # Close chat-container

        # Chat input (outside the containers for better positioning)
        user_input = st.chat_input(
            "Type your message here... (e.g., 'Show me my business statistics' or 'Find invoices for Acme Corp')"
        )

        if user_input:
            self._handle_user_input(user_input)

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

    def _display_notifications(self):
        """Display notifications."""
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
        """Handle user input."""
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

        # Rerun to update display
        st.rerun()

    def _process_user_input(self, user_input: str) -> str:
        """Process user input using conversational AI."""
        try:
            # Get conversation history (excluding the current message)
            conversation_history = (
                st.session_state.messages[:-1]
                if len(st.session_state.messages) > 1
                else []
            )

            # Use the AI conversation component for real conversational responses
            response = self.ai_chat.process_conversation(
                user_input, conversation_history
            )

            return response

        except Exception as e:
            return f"❌ I encountered an error while processing your request: {str(e)}. Please try again or contact support."

    def _handle_real_time_updates(self):
        """Handle real-time updates."""
        if st.session_state.get("auto_refresh", False):
            time_since_refresh = datetime.now() - st.session_state.get(
                "last_refresh", datetime.now()
            )
            if time_since_refresh.total_seconds() > 30:
                st.session_state.last_refresh = datetime.now()
                st.rerun()

    def _handle_analytics_chat(self, user_input: str):
        """Handle chat input for analytics page."""
        try:
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

            # Rerun to update display
            st.rerun()

        except Exception as e:
            st.error(f"Error processing analytics chat: {str(e)}")
            # Still add the user message even if processing fails
            if user_input not in [
                msg.get("content", "") for msg in st.session_state.messages[-5:]
            ]:
                st.session_state.messages.append(
                    {"role": "user", "content": user_input, "timestamp": datetime.now()}
                )
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"❌ Sorry, I encountered an error: {str(e)}",
                        "timestamp": datetime.now(),
                    }
                )
            st.rerun()


def main():
    """Main function to run the application."""
    try:
        app = ModernInvoiceApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please refresh the page or contact support if the problem persists.")


if __name__ == "__main__":
    main()
