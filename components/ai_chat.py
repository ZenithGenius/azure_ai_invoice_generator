"""
AI Chat Component for Invoice Management Dashboard
=================================================

Provides conversational AI capabilities using Azure AI Foundry.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import re
from azure.ai.agents.models import ListSortOrder


class AIConversationComponent:
    """Handles conversational AI interactions using Azure AI Foundry."""

    def __init__(self, service_manager):
        """Initialize AI conversation component."""
        self.service_manager = service_manager
        self._initialize_conversation_context()

    def _initialize_conversation_context(self):
        """Initialize conversation context and system prompt."""
        self.system_prompt = """You are an intelligent AI assistant for an Invoice Management System. You help users with:

1. **Invoice Operations**: Generate, search, update, and manage invoices
2. **Business Analytics**: Provide insights, statistics, and data analysis
3. **System Help**: Guide users through features and functionality
4. **Data Queries**: Answer questions about business data and performance

**Your Capabilities:**
- Access to invoice database for searching and retrieving information
- Real-time business statistics and analytics
- Invoice generation assistance
- System status and health monitoring
- Conversational help and guidance

**Response Style:**
- Be conversational and helpful
- Use emojis appropriately for better UX
- Provide specific data when available
- Offer actionable suggestions
- Ask clarifying questions when needed
- Keep responses concise but informative

**Available Data:**
- Invoice records with client information, amounts, dates, status
- Business statistics (totals, averages, trends)
- System performance metrics
- Cache and service status

**Current Context:**
You are integrated into a Streamlit dashboard with navigation to:
- Chat Assistant (current page)
- Analytics Dashboard
- Quick Invoice Generator
- System Status

Always be helpful and provide accurate information based on the available data."""

    def process_conversation(
        self, user_input: str, conversation_history: List[Dict]
    ) -> str:
        """Process user input and generate conversational AI response."""
        try:
            # Enhanced AI service availability check
            if not (self.service_manager.is_service_available("ai_project") and 
                   self.service_manager.is_service_available("agent")):
                # Test AI connectivity for better error reporting
                ai_status = self.service_manager.test_ai_connectivity()
                error_msg = ai_status.get("error", "AI services unavailable")
                return self._fallback_response(user_input, error_msg)

            # Get AI client and agent with enhanced validation
            ai_client = self.service_manager.get_ai_project_client()
            agent = self.service_manager.get_agent()

            if not ai_client or not agent:
                return self._fallback_response(user_input, "AI client or agent not properly initialized")

            # Create conversation thread
            thread = ai_client.agents.threads.create()

            # Build conversation context
            context = self._build_conversation_context(user_input)

            # Create the conversation message with enhanced context
            conversation_message = f"""
{self.system_prompt}

**Current Business Data:**
{context}

**Conversation History:**
{self._format_conversation_history(conversation_history[-5:])}

**User Question:** {user_input}

Please provide a helpful, conversational response based on the available data and context. Be specific and use the actual data provided. If the user is asking for data that's available in the context, provide exact numbers and details.
"""

            # Send message to AI with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    message = ai_client.agents.messages.create(
                        thread_id=thread.id, role="user", content=conversation_message
                    )

                    # Run the agent with enhanced instructions
                    run = ai_client.agents.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=agent.id,
                        instructions="""You are an intelligent invoice management assistant. Provide conversational, helpful responses using the specific business data provided. 

Key guidelines:
- Use actual numbers and data from the context when available
- Be conversational and friendly
- Provide actionable insights and suggestions
- If asked about specific invoices or clients, use the search results provided
- Format responses clearly with emojis for better readability
- Always be helpful and specific rather than generic

Respond naturally as if you're a knowledgeable business assistant who has access to all the invoice data.""",
                    )

                    if run.status == "completed":
                        # Get the response
                        messages = ai_client.agents.messages.list(
                            thread_id=thread.id, order=ListSortOrder.ASCENDING
                        )

                        # Extract AI response
                        assistant_messages = [msg for msg in messages if msg.role == "assistant"]
                        if assistant_messages:
                            last_message = assistant_messages[-1]
                            if last_message.text_messages:
                                ai_response = last_message.text_messages[-1].text.value
                                cleaned_response = self._clean_ai_response(ai_response)
                                
                                # Validate response quality
                                if len(cleaned_response.strip()) > 20:  # Ensure substantial response
                                    return cleaned_response
                    
                    elif run.status == "failed":
                        if attempt == max_retries - 1:  # Last attempt
                            return self._fallback_response(
                                user_input, f"AI processing failed: {run.last_error}"
                            )
                        continue  # Retry
                    
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        return self._fallback_response(user_input, f"AI request failed: {str(e)}")
                    continue  # Retry

            return self._fallback_response(user_input, "AI response generation failed after retries")

        except Exception as e:
            return self._fallback_response(user_input, f"Unexpected error: {str(e)}")

    def _build_conversation_context(self, user_input: str) -> str:
        """Build context with current business data for the AI."""
        context_parts = []

        try:
            # Get current statistics
            stats = self.service_manager.get_statistics()
            context_parts.append(f"""
**Business Statistics:**
- Total Invoices: {stats.get('total_invoices', 0)}
- Outstanding Amount: ${stats.get('total_outstanding_amount', 0):,.2f}
- Recent Invoices (30 days): {stats.get('recent_invoices_30_days', 0)}
- Average Invoice Amount: ${stats.get('average_invoice_amount', 0):,.2f}
""")

            # Get system status
            status = self.service_manager.get_service_status_cached()
            services = status.get("services_available", {})
            online_services = sum(services.values())
            total_services = len(services)
            context_parts.append(f"""
**System Status:**
- Services Online: {online_services}/{total_services}
- AI Project: {'✅' if services.get('ai_project') else '❌'}
- Database: {'✅' if services.get('cosmos') else '❌'}
- Search: {'✅' if services.get('search') else '❌'}
""")

            # If user mentions specific search terms, get relevant data
            if any(
                keyword in user_input.lower()
                for keyword in ["search", "find", "client", "invoice"]
            ):
                search_terms = self._extract_search_terms(user_input)
                if search_terms:
                    try:
                        search_results = self.service_manager.search_invoices(
                            search_terms
                        )
                        if search_results:
                            context_parts.append(f"""
**Relevant Invoice Data for '{search_terms}':**
{self._format_search_results(search_results[:3])}  # Top 3 results
""")
                    except Exception:
                        pass  # Don't fail if search doesn't work

            # Get cache performance
            cache_stats = self.service_manager.get_cache_statistics()
            perf = cache_stats.get("performance", {})
            context_parts.append(f"""
**System Performance:**
- Cache Hit Rate: {perf.get('hit_rate_percent', 0):.1f}%
- Total Requests: {perf.get('total_requests', 0):,}
""")

        except Exception as e:
            context_parts.append(f"**Note:** Some data unavailable due to: {str(e)}")

        return "\n".join(context_parts)

    def _extract_search_terms(self, user_input: str) -> Optional[str]:
        """Extract search terms from user input."""
        # Remove common words and extract meaningful terms
        user_input_lower = user_input.lower()

        # Look for quoted terms first
        quoted_terms = re.findall(r'"([^"]*)"', user_input)
        if quoted_terms:
            return quoted_terms[0]

        # Look for specific patterns
        patterns = [
            r"(?:search|find|look for|show me)\s+(?:invoices?\s+)?(?:for\s+)?([a-zA-Z0-9\s]+?)(?:\s|$)",
            r"(?:client|company)\s+(?:named?\s+)?([a-zA-Z0-9\s]+?)(?:\s|$)",
            r"invoice\s+(?:number\s+)?([a-zA-Z0-9-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                term = match.group(1).strip()
                if len(term) > 2:  # Only return meaningful terms
                    return term

        return None

    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for context."""
        if not results:
            return "No matching invoices found."

        formatted = []
        for invoice in results:
            invoice_num = invoice.get("invoice_number", "N/A")
            client_name = invoice.get("client", {}).get("name", "Unknown")
            total = invoice.get("total", 0)
            status = invoice.get("status", "unknown")
            date = invoice.get("invoice_date", "N/A")

            formatted.append(
                f"- {invoice_num}: {client_name} - ${total:,.2f} ({status}) - {date}"
            )

        return "\n".join(formatted)

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format recent conversation history for context."""
        if not history:
            return "No previous conversation."

        formatted = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Limit length
            timestamp = msg.get("timestamp", datetime.now()).strftime("%H:%M")
            formatted.append(f"{timestamp} - {role.title()}: {content}")

        return "\n".join(formatted)

    def _clean_ai_response(self, response: str) -> str:
        """Clean and format AI response."""
        # Remove any system prompt echoes or unwanted formatting
        response = response.strip()

        # Remove common AI response prefixes
        prefixes_to_remove = [
            "Based on the provided data,",
            "According to the business data,",
            "Looking at the current statistics,",
        ]

        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix) :].strip()

        # Ensure response starts with appropriate greeting if it's too abrupt
        if not any(
            response.startswith(greeting)
            for greeting in [
                "Hi",
                "Hello",
                "Sure",
                "I can",
                "Let me",
                "Here",
                "Based",
                "Looking",
                "According",
            ]
        ):
            if "?" in response:
                response = f"Great question! {response}"
            else:
                response = f"I can help with that. {response}"

        return response

    def _fallback_response(self, user_input: str, error: str = None) -> str:
        """Generate automated response when primary AI is unavailable."""
        try:
            # Try to use a simpler AI approach or local processing
            context = self._build_conversation_context(user_input)

            # Create a simplified automated response based on context and user input
            response_parts = []

            # Add greeting
            response_parts.append("🤖 I'm here to help!")

            # Analyze user input and provide relevant data
            user_input_lower = user_input.lower()

            if any(
                keyword in user_input_lower
                for keyword in ["statistics", "stats", "numbers", "data"]
            ):
                try:
                    stats = self.service_manager.get_statistics()
                    response_parts.append(f"""
📊 **Current Business Statistics:**
• Total Invoices: {stats.get('total_invoices', 0):,}
• Outstanding Amount: ${stats.get('total_outstanding_amount', 0):,.2f}
• Recent Activity: {stats.get('recent_invoices_30_days', 0)} invoices (30 days)
• Average Invoice: ${stats.get('average_invoice_amount', 0):,.2f}
""")
                except Exception:
                    response_parts.append(
                        "📊 I'm having trouble accessing your statistics right now."
                    )

            elif any(
                keyword in user_input_lower for keyword in ["search", "find", "look"]
            ):
                # Try to extract search terms and perform search
                search_terms = self._extract_search_terms(user_input)
                if search_terms:
                    try:
                        results = self.service_manager.search_invoices(search_terms)
                        if results:
                            response_parts.append(
                                f"🔍 **Found {len(results)} results for '{search_terms}':**"
                            )
                            response_parts.append(
                                self._format_search_results(results[:3])
                            )
                        else:
                            response_parts.append(
                                f"🔍 No invoices found matching '{search_terms}'. Try different search terms."
                            )
                    except Exception:
                        response_parts.append(
                            "🔍 Search functionality is temporarily unavailable."
                        )
                else:
                    response_parts.append(
                        "🔍 Please specify what you'd like to search for (client name, invoice number, etc.)"
                    )

            elif any(
                keyword in user_input_lower
                for keyword in ["generate", "create", "new invoice"]
            ):
                response_parts.append("""📝 **Ready to create a new invoice!**
                
Use the Quick Invoice Generator in the navigation menu, or tell me:
• Client name and details
• Services or products provided  
• Amounts and quantities
• Any special terms or notes

I'll help you structure everything properly.""")

            elif any(
                keyword in user_input_lower
                for keyword in ["help", "how", "what can you do"]
            ):
                response_parts.append("""💡 **I can help you with:**

📋 **Invoice Management:**
• Generate professional invoices
• Search and find existing invoices  
• Update invoice status
• Export invoice data

📊 **Business Analytics:**
• View statistics and metrics
• Analyze revenue trends
• Monitor outstanding payments
• Generate insights

🔧 **System Operations:**
• Check system health
• Monitor performance
• Troubleshoot issues

Just ask me naturally - I understand conversational requests!""")

            else:
                # Generate a contextual response based on available data
                response_parts.append(
                    f"I understand you're asking about: **{user_input}**"
                )

                # Add relevant context if available
                try:
                    stats = self.service_manager.get_statistics()
                    if stats.get("total_invoices", 0) > 0:
                        response_parts.append(f"""
📊 **Quick Context:**
• You have {stats.get('total_invoices', 0)} total invoices
• ${stats.get('total_outstanding_amount', 0):,.2f} outstanding
• {stats.get('recent_invoices_30_days', 0)} recent invoices

How can I help you with your invoice management today?""")
                except Exception:
                    response_parts.append(
                        "How can I help you with your invoice management today?"
                    )

            # Add helpful suggestions
            response_parts.append("""
💡 **Try asking me:**
• "Show me my business statistics"
• "Find invoices for [client name]"  
• "Help me create a new invoice"
• "What's my outstanding balance?"
""")

            if error:
                response_parts.append(
                    f"*Note: Advanced AI features temporarily limited ({error})*"
                )

            return "\n".join(response_parts)

        except Exception as e:
            # Ultimate fallback
            return f"""🤖 I'm here to help with your invoice management!

While I'm experiencing some technical difficulties, I can still assist you with basic operations through the navigation menu:

• **Analytics Dashboard** - View your business data
• **Quick Invoice** - Generate new invoices  
• **System Status** - Check service health

Please try your request again, or use the menu options above.

*Technical note: {str(e) if error else 'Service temporarily limited'}*"""

    def suggest_follow_up_questions(
        self, user_input: str, ai_response: str
    ) -> List[str]:
        """Suggest relevant follow-up questions based on the conversation."""
        suggestions = []

        user_input_lower = user_input.lower()

        if "statistics" in user_input_lower or "stats" in user_input_lower:
            suggestions.extend(
                [
                    "Show me trends for the last 3 months",
                    "Which clients owe the most money?",
                    "What's my average payment time?",
                ]
            )

        elif "search" in user_input_lower or "find" in user_input_lower:
            suggestions.extend(
                [
                    "Show me all unpaid invoices",
                    "Find invoices over $1000",
                    "What invoices are overdue?",
                ]
            )

        elif "invoice" in user_input_lower and "create" in user_input_lower:
            suggestions.extend(
                [
                    "What information do I need for an invoice?",
                    "Can you help me with invoice templates?",
                    "How do I set up recurring invoices?",
                ]
            )

        else:
            # General suggestions
            suggestions.extend(
                [
                    "Show me my business statistics",
                    "Find recent invoices",
                    "How do I create a new invoice?",
                    "What's my system status?",
                ]
            )

        return suggestions[:3]  # Return top 3 suggestions
 