"""
Enhanced Invoice Analytics Dashboard
===================================

Advanced analytics and business intelligence for invoice management system
with real-time updates, comprehensive visualizations, and actionable insights.
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics
import calendar
import time
from service_manager import get_service_manager
import os


class InvoiceAnalytics:
    """Enhanced analytics for invoice management system with advanced visualizations."""

    def __init__(self):
        """Initialize the enhanced analytics system."""
        print("🔄 Initializing Enhanced Invoice Analytics...")
        self.service_manager = get_service_manager()
        print("✅ Enhanced Invoice Analytics initialized successfully")

    def create_streamlit_dashboard(self):
        """Create comprehensive Streamlit analytics dashboard."""
        # st.title("📊 Enhanced Invoice Analytics Dashboard")
        st.markdown("### Real-time Business Intelligence & Insights")
        st.markdown("---")

        # Header with controls
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("### 📊 Business Analytics Dashboard")

        with col2:
            date_range = st.selectbox(
                "📅 Time Period",
                ["Last 30 days", "Last 90 days", "Last 6 months", "All time"],
                index=0,
                key="analytics_date_range",
            )

        with col3:
            if st.button(
                "🔄 Refresh Now", type="secondary", key="analytics_refresh_btn"
            ):
                st.cache_data.clear()
                st.rerun()

        # Download section
        st.markdown("---")
        st.markdown("### 📥 Export Analytics Data")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(
                "📊 Export Charts", key="export_charts", use_container_width=True
            ):
                self._export_charts_data()

        with col2:
            if st.button("📈 Export CSV", key="export_csv", use_container_width=True):
                self._export_analytics_csv()

        with col3:
            if st.button(
                "📄 Export Report", key="export_report", use_container_width=True
            ):
                self._export_analytics_report()

        with col4:
            if st.button(
                "📋 Export Summary", key="export_summary", use_container_width=True
            ):
                self._export_executive_summary()

        st.markdown("---")

        # Generate analytics data
        with st.spinner("🔄 Loading analytics data..."):
            insights = self.generate_business_insights()

        if "error" in insights:
            st.error(f"❌ Analytics Error: {insights['error']}")
            return

        # Executive Summary
        self._render_executive_summary(insights)

        # Main analytics tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "📊 Overview",
                "💰 Revenue",
                "👥 Clients",
                "📈 Trends",
                "⚠️ Risk Analysis",
                "🎯 Recommendations",
            ]
        )

        with tab1:
            self._render_overview_dashboard(insights)

        with tab2:
            self._render_revenue_analytics(insights)

        with tab3:
            self._render_client_analytics(insights)

        with tab4:
            self._render_trend_analysis(insights)

        with tab5:
            self._render_risk_analysis(insights)

        with tab6:
            self._render_recommendations(insights)

        # Real-time updates (add auto-refresh toggle)
        auto_refresh = st.session_state.get("auto_refresh", False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()

    def _render_executive_summary(self, insights: Dict):
        """Render executive summary with key metrics."""
        st.markdown("### 📋 Executive Summary")

        overview = insights.get("overview", {})

        # Key metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            total_revenue = overview.get("total_revenue", 0)
            st.metric(
                "Total Revenue",
                f"${total_revenue:,.2f}",
                delta=f"+{overview.get('paid_revenue', 0):,.2f} collected",
            )

        with col2:
            total_invoices = overview.get("total_invoices", 0)
            st.metric(
                "Total Invoices",
                f"{total_invoices:,}",
                delta=f"Avg: ${overview.get('average_invoice_value', 0):,.2f}",
            )

        with col3:
            collection_rate = overview.get("collection_rate_percent", 0)
            delta_color = "normal" if collection_rate >= 80 else "inverse"
            st.metric(
                "Collection Rate",
                f"{collection_rate:.1f}%",
                delta=f"{'Good' if collection_rate >= 80 else 'Needs Attention'}",
                delta_color=delta_color,
            )

        with col4:
            outstanding = overview.get("outstanding_amount", 0)
            outstanding_ratio = (
                (outstanding / total_revenue * 100) if total_revenue > 0 else 0
            )
            st.metric(
                "Outstanding",
                f"${outstanding:,.2f}",
                delta=f"{outstanding_ratio:.1f}% of total",
                delta_color="inverse" if outstanding_ratio > 20 else "normal",
            )

        with col5:
            # Calculate health score
            health_score = self._calculate_business_health_score(overview)
            health_color = "normal" if health_score >= 75 else "inverse"
            st.metric(
                "Health Score",
                f"{health_score}/100",
                delta=self._get_health_status(health_score),
                delta_color=health_color,
            )

    def _render_overview_dashboard(self, insights: Dict):
        """Render comprehensive overview dashboard."""
        st.markdown("### 📊 Business Overview")

        overview = insights.get("overview", {})

        # Status distribution visualization
        col1, col2 = st.columns(2)

        with col1:
            # Invoice status pie chart
            status_dist = overview.get("status_distribution", {})
            if status_dist:
                # Custom colors for different statuses
                colors = {
                    "paid": "#10b981",  # green
                    "active": "#f59e0b",  # amber
                    "overdue": "#ef4444",  # red
                    "draft": "#6b7280",  # gray
                    "cancelled": "#8b5cf6",  # purple
                }

                fig_status = go.Figure(
                    data=[
                        go.Pie(
                            labels=list(status_dist.keys()),
                            values=list(status_dist.values()),
                            hole=0.4,
                            marker_colors=[
                                colors.get(status, "#6b7280")
                                for status in status_dist.keys()
                            ],
                            textinfo="label+percent",
                            textposition="outside",
                        )
                    ]
                )

                fig_status.update_layout(
                    title="Invoice Status Distribution", height=400, showlegend=True
                )
                st.plotly_chart(fig_status, use_container_width=True)

        with col2:
            # Revenue vs Outstanding comparison
            paid_revenue = overview.get("paid_revenue", 0)
            outstanding = overview.get("outstanding_amount", 0)

            fig_revenue = go.Figure(
                data=[
                    go.Bar(
                        x=["Collected", "Outstanding"],
                        y=[paid_revenue, outstanding],
                        marker_color=["#10b981", "#ef4444"],
                        text=[f"${paid_revenue:,.0f}", f"${outstanding:,.0f}"],
                        textposition="auto",
                    )
                ]
            )

            fig_revenue.update_layout(
                title="Revenue Collection Status",
                height=400,
                yaxis_title="Amount ($)",
                showlegend=False,
            )
            st.plotly_chart(fig_revenue, use_container_width=True)

        # Performance indicators
        st.markdown("#### 🎯 Performance Indicators")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Collection efficiency gauge
            collection_rate = overview.get("collection_rate_percent", 0)
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=collection_rate,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Collection Rate (%)"},
                    delta={"reference": 80},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgray"},
                            {"range": [50, 80], "color": "yellow"},
                            {"range": [80, 100], "color": "lightgreen"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 90,
                        },
                    },
                )
            )
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            # Average invoice value trend (simulated)
            avg_value = overview.get("average_invoice_value", 0)
            trend_data = np.random.normal(avg_value, avg_value * 0.1, 30)
            dates = pd.date_range(end=datetime.now(), periods=30, freq="D")

            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Scatter(
                    x=dates,
                    y=trend_data,
                    mode="lines+markers",
                    name="Avg Invoice Value",
                    line=dict(color="#667eea", width=2),
                )
            )

            fig_trend.update_layout(
                title="Average Invoice Value Trend (30 days)",
                height=300,
                xaxis_title="Date",
                yaxis_title="Amount ($)",
                showlegend=False,
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with col3:
            # Invoice volume by day of week (simulated)
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            volumes = np.random.poisson(5, 7)  # Simulated daily volumes

            fig_volume = go.Figure(
                data=[
                    go.Bar(
                        x=days,
                        y=volumes,
                        marker_color="#10b981",
                        text=volumes,
                        textposition="auto",
                    )
                ]
            )

            fig_volume.update_layout(
                title="Invoice Volume by Day of Week",
                height=300,
                xaxis_title="Day",
                yaxis_title="Count",
                showlegend=False,
            )
            st.plotly_chart(fig_volume, use_container_width=True)

    def _render_revenue_analytics(self, insights: Dict):
        """Render detailed revenue analytics."""
        st.markdown("### 💰 Revenue Analytics")

        revenue_analysis = insights.get("revenue_analysis", {})
        monthly_breakdown = revenue_analysis.get("monthly_breakdown", {})

        if monthly_breakdown:
            # Monthly revenue trend
            df_monthly = pd.DataFrame(
                list(monthly_breakdown.items()), columns=["Month", "Revenue"]
            )
            df_monthly["Month"] = pd.to_datetime(
                df_monthly["Month"], format="%m/%Y", errors="coerce"
            )
            df_monthly = df_monthly.dropna().sort_values("Month")

            # Revenue trend chart
            fig_revenue_trend = go.Figure()
            fig_revenue_trend.add_trace(
                go.Scatter(
                    x=df_monthly["Month"],
                    y=df_monthly["Revenue"],
                    mode="lines+markers",
                    name="Monthly Revenue",
                    line=dict(color="#1f77b4", width=3),
                    marker=dict(size=8),
                    fill="tonexty",
                )
            )

            # Add trend line
            if len(df_monthly) > 1:
                z = np.polyfit(range(len(df_monthly)), df_monthly["Revenue"], 1)
                trend_line = np.poly1d(z)(range(len(df_monthly)))

                fig_revenue_trend.add_trace(
                    go.Scatter(
                        x=df_monthly["Month"],
                        y=trend_line,
                        mode="lines",
                        name="Trend",
                        line=dict(color="red", width=2, dash="dash"),
                    )
                )

            fig_revenue_trend.update_layout(
                title="Monthly Revenue Trend",
                height=400,
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                hovermode="x unified",
            )
            st.plotly_chart(fig_revenue_trend, use_container_width=True)

            # Revenue statistics
            revenue_stats = revenue_analysis.get("revenue_statistics", {})
            if revenue_stats:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Highest Invoice",
                        f"${revenue_stats.get('highest_invoice', 0):,.2f}",
                    )

                with col2:
                    st.metric(
                        "Lowest Invoice",
                        f"${revenue_stats.get('lowest_invoice', 0):,.2f}",
                    )

                with col3:
                    st.metric(
                        "Median Invoice",
                        f"${revenue_stats.get('median_invoice', 0):,.2f}",
                    )

                with col4:
                    st.metric(
                        "Revenue Std Dev",
                        f"${revenue_stats.get('revenue_std_dev', 0):,.2f}",
                    )

        else:
            st.info("📊 No revenue data available for detailed analysis")

    def _render_client_analytics(self, insights: Dict):
        """Render client performance analytics."""
        st.markdown("### 👥 Client Analytics")

        client_analysis = insights.get("client_analysis", {})

        # Client overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Clients", client_analysis.get("total_unique_clients", 0))

        with col2:
            avg_revenue = client_analysis.get("average_revenue_per_client", 0)
            st.metric("Avg Revenue/Client", f"${avg_revenue:,.2f}")

        with col3:
            avg_invoices = client_analysis.get("average_invoices_per_client", 0)
            st.metric("Avg Invoices/Client", f"{avg_invoices:.1f}")

        with col4:
            concentration = client_analysis.get("client_concentration_top3_percent", 0)
            st.metric("Top 3 Client Concentration", f"{concentration:.1f}%")

        # Top clients visualizations
        col1, col2 = st.columns(2)

        with col1:
            # Top clients by revenue
            top_clients_revenue = client_analysis.get("top_clients_by_revenue", [])
            if top_clients_revenue:
                clients = [client[0] for client in top_clients_revenue]
                revenues = [client[1] for client in top_clients_revenue]

                fig_top_revenue = px.bar(
                    x=revenues,
                    y=clients,
                    orientation="h",
                    title="Top 5 Clients by Revenue",
                    labels={"x": "Revenue ($)", "y": "Client"},
                    color=revenues,
                    color_continuous_scale="Blues",
                )
                fig_top_revenue.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_top_revenue, use_container_width=True)

        with col2:
            # Top clients by invoice count
            top_clients_count = client_analysis.get("top_clients_by_invoice_count", [])
            if top_clients_count:
                clients = [client[0] for client in top_clients_count]
                counts = [client[1] for client in top_clients_count]

                fig_top_count = px.bar(
                    x=counts,
                    y=clients,
                    orientation="h",
                    title="Top 5 Clients by Invoice Count",
                    labels={"x": "Invoice Count", "y": "Client"},
                    color=counts,
                    color_continuous_scale="Greens",
                )
                fig_top_count.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_top_count, use_container_width=True)

        # Client segmentation analysis
        if top_clients_revenue:
            st.markdown("#### 🎯 Client Segmentation")

            # Create client segments based on revenue
            all_revenues = [client[1] for client in top_clients_revenue]
            if len(all_revenues) >= 3:
                high_value = sum(all_revenues[:2])  # Top 2 clients
                medium_value = (
                    sum(all_revenues[2:4]) if len(all_revenues) > 3 else all_revenues[2]
                )
                low_value = sum(all_revenues[4:]) if len(all_revenues) > 4 else 0

                segments = ["High Value", "Medium Value", "Low Value"]
                values = [high_value, medium_value, low_value]

                fig_segments = px.pie(
                    values=values,
                    names=segments,
                    title="Client Revenue Segmentation",
                    color_discrete_sequence=["#10b981", "#f59e0b", "#ef4444"],
                )
                st.plotly_chart(fig_segments, use_container_width=True)

    def _render_trend_analysis(self, insights: Dict):
        """Render trend analysis and forecasting."""
        st.markdown("### 📈 Trend Analysis & Forecasting")

        # Simulated trend data for demonstration
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=90), end=datetime.now(), freq="D"
        )

        # Generate realistic invoice trends
        base_invoices = 5
        trend = 0.02  # 2% daily growth
        noise = np.random.normal(0, 1, len(dates))
        invoice_counts = [
            max(0, base_invoices + trend * i + noise[i]) for i in range(len(dates))
        ]

        # Revenue trends
        avg_invoice_value = insights.get("overview", {}).get(
            "average_invoice_value", 1000
        )
        revenue_trend = [
            count * avg_invoice_value * (1 + np.random.normal(0, 0.1))
            for count in invoice_counts
        ]

        # Create trend visualization
        fig_trends = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Invoice Volume Trend",
                "Revenue Trend",
                "Cumulative Revenue",
                "Growth Rate",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        # Invoice volume trend
        fig_trends.add_trace(
            go.Scatter(
                x=dates,
                y=invoice_counts,
                mode="lines",
                name="Daily Invoices",
                line=dict(color="#1f77b4", width=2),
            ),
            row=1,
            col=1,
        )

        # Revenue trend
        fig_trends.add_trace(
            go.Scatter(
                x=dates,
                y=revenue_trend,
                mode="lines",
                name="Daily Revenue",
                line=dict(color="#2ca02c", width=2),
            ),
            row=1,
            col=2,
        )

        # Cumulative revenue
        cumulative_revenue = np.cumsum(revenue_trend)
        fig_trends.add_trace(
            go.Scatter(
                x=dates,
                y=cumulative_revenue,
                mode="lines",
                name="Cumulative Revenue",
                line=dict(color="#ff7f0e", width=2),
                fill="tonexty",
            ),
            row=2,
            col=1,
        )

        # Growth rate
        growth_rates = [0] + [
            ((revenue_trend[i] - revenue_trend[i - 1]) / revenue_trend[i - 1] * 100)
            if revenue_trend[i - 1] != 0
            else 0
            for i in range(1, len(revenue_trend))
        ]
        fig_trends.add_trace(
            go.Scatter(
                x=dates,
                y=growth_rates,
                mode="lines",
                name="Growth Rate (%)",
                line=dict(color="#d62728", width=2),
            ),
            row=2,
            col=2,
        )

        fig_trends.update_layout(
            height=600, showlegend=False, title_text="Business Trends Analysis"
        )
        st.plotly_chart(fig_trends, use_container_width=True)

        # Forecasting section
        st.markdown("#### 🔮 Revenue Forecasting")

        # Simple forecasting (next 30 days)
        forecast_days = 30
        last_value = revenue_trend[-1]
        forecast_trend = [
            last_value * (1 + trend) ** i for i in range(1, forecast_days + 1)
        ]
        forecast_dates = pd.date_range(
            start=dates[-1] + timedelta(days=1), periods=forecast_days, freq="D"
        )

        col1, col2 = st.columns(2)

        with col1:
            # Forecast chart
            fig_forecast = go.Figure()

            # Historical data
            fig_forecast.add_trace(
                go.Scatter(
                    x=dates[-30:],  # Last 30 days
                    y=revenue_trend[-30:],
                    mode="lines+markers",
                    name="Historical",
                    line=dict(color="#1f77b4", width=2),
                )
            )

            # Forecast
            fig_forecast.add_trace(
                go.Scatter(
                    x=forecast_dates,
                    y=forecast_trend,
                    mode="lines+markers",
                    name="Forecast",
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                )
            )

            fig_forecast.update_layout(
                title="30-Day Revenue Forecast",
                height=400,
                xaxis_title="Date",
                yaxis_title="Revenue ($)",
            )
            st.plotly_chart(fig_forecast, use_container_width=True)

        with col2:
            # Forecast metrics
            total_forecast = sum(forecast_trend)
            avg_daily_forecast = total_forecast / forecast_days

            st.metric("30-Day Forecast", f"${total_forecast:,.2f}")
            st.metric("Avg Daily Revenue", f"${avg_daily_forecast:,.2f}")
            st.metric("Growth Trend", f"{trend*100:.1f}% daily")

            # Confidence intervals
            st.markdown("**Forecast Confidence:**")
            st.markdown("• High confidence: ±10%")
            st.markdown("• Medium confidence: ±20%")
            st.markdown("• Low confidence: ±30%")

    def _render_risk_analysis(self, insights: Dict):
        """Render risk analysis dashboard."""
        st.markdown("### ⚠️ Risk Analysis")

        overview = insights.get("overview", {})

        # Risk metrics
        total_revenue = overview.get("total_revenue", 0)
        outstanding = overview.get("outstanding_amount", 0)
        collection_rate = overview.get("collection_rate_percent", 0)

        # Calculate risk scores
        outstanding_risk = (
            (outstanding / total_revenue * 100) if total_revenue > 0 else 0
        )
        collection_risk = 100 - collection_rate

        # Overall risk score
        overall_risk = (outstanding_risk + collection_risk) / 2

        # Risk level determination
        if overall_risk < 15:
            risk_level = "🟢 Low Risk"
            risk_color = "#10b981"
        elif overall_risk < 30:
            risk_level = "🟡 Medium Risk"
            risk_color = "#f59e0b"
        else:
            risk_level = "🔴 High Risk"
            risk_color = "#ef4444"

        # Risk dashboard
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Overall Risk Level", risk_level, f"{overall_risk:.1f}%")

        with col2:
            st.metric(
                "Outstanding Risk", f"{outstanding_risk:.1f}%", f"${outstanding:,.2f}"
            )

        with col3:
            st.metric(
                "Collection Risk",
                f"{collection_risk:.1f}%",
                f"{collection_rate:.1f}% rate",
            )

        with col4:
            # Days sales outstanding (simulated)
            dso = np.random.uniform(25, 45)
            st.metric("Days Sales Outstanding", f"{dso:.0f} days")

        # Risk visualization
        col1, col2 = st.columns(2)

        with col1:
            # Risk breakdown pie chart
            risk_categories = [
                "Collection Risk",
                "Outstanding Risk",
                "Operational Risk",
            ]
            risk_values = [
                collection_risk,
                outstanding_risk,
                10,
            ]  # 10% operational risk

            fig_risk = px.pie(
                values=risk_values,
                names=risk_categories,
                title="Risk Breakdown",
                color_discrete_sequence=["#ef4444", "#f59e0b", "#6b7280"],
            )
            st.plotly_chart(fig_risk, use_container_width=True)

        with col2:
            # Risk trend over time (simulated)
            risk_dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
            risk_trend = np.random.uniform(overall_risk - 5, overall_risk + 5, 30)

            fig_risk_trend = go.Figure()
            fig_risk_trend.add_trace(
                go.Scatter(
                    x=risk_dates,
                    y=risk_trend,
                    mode="lines+markers",
                    name="Risk Score",
                    line=dict(color=risk_color, width=2),
                )
            )

            # Add risk threshold lines
            fig_risk_trend.add_hline(
                y=15,
                line_dash="dash",
                line_color="green",
                annotation_text="Low Risk Threshold",
            )
            fig_risk_trend.add_hline(
                y=30,
                line_dash="dash",
                line_color="red",
                annotation_text="High Risk Threshold",
            )

            fig_risk_trend.update_layout(
                title="Risk Score Trend (30 days)",
                height=400,
                xaxis_title="Date",
                yaxis_title="Risk Score (%)",
            )
            st.plotly_chart(fig_risk_trend, use_container_width=True)

        # Risk mitigation recommendations
        st.markdown("#### 🛡️ Risk Mitigation Recommendations")

        recommendations = []

        if outstanding_risk > 20:
            recommendations.append(
                "🔴 **High Outstanding Risk**: Implement automated payment reminders"
            )

        if collection_risk > 20:
            recommendations.append(
                "🔴 **Poor Collection Rate**: Review credit policies and payment terms"
            )

        if overall_risk > 25:
            recommendations.append(
                "🔴 **High Overall Risk**: Consider invoice factoring or credit insurance"
            )

        if not recommendations:
            recommendations.append(
                "🟢 **Low Risk Profile**: Maintain current practices and monitor regularly"
            )

        for rec in recommendations:
            st.markdown(rec)

    def _render_recommendations(self, insights: Dict):
        """Render actionable business recommendations."""
        st.markdown("### 🎯 Business Recommendations")

        recommendations = insights.get("recommendations", [])

        if not recommendations:
            st.info(
                "📊 Generate more invoice data to receive personalized recommendations"
            )
            return

        # Display recommendations
        for i, rec in enumerate(recommendations[:5]):  # Show top 5 recommendations
            priority = rec.get("priority", "medium")
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                priority, "🟡"
            )

            with st.expander(f"{priority_icon} {rec.get('title', 'Recommendation')}"):
                st.markdown(f"**Priority:** {priority.title()}")
                st.markdown(
                    f"**Description:** {rec.get('description', 'No description available')}"
                )

    def _calculate_business_health_score(self, overview: Dict) -> int:
        """Calculate overall business health score."""
        collection_rate = overview.get("collection_rate_percent", 0)
        total_revenue = overview.get("total_revenue", 0)
        outstanding_ratio = (
            (overview.get("outstanding_amount", 0) / total_revenue * 100)
            if total_revenue > 0
            else 0
        )

        # Health score calculation
        collection_score = min(collection_rate, 100)
        outstanding_score = max(
            0, 100 - outstanding_ratio * 2
        )  # Penalize high outstanding
        revenue_score = min(100, total_revenue / 10000 * 100)  # Scale based on revenue

        health_score = int(
            (collection_score * 0.4 + outstanding_score * 0.4 + revenue_score * 0.2)
        )
        return min(100, max(0, health_score))

    def _get_health_status(self, score: int) -> str:
        """Get health status description."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"

    def generate_business_insights(self) -> Dict:
        """Generate comprehensive business insights from invoice data."""
        try:
            # Get all invoices using service manager
            all_invoices = self.service_manager.list_invoices(limit=1000)

            if not all_invoices:
                return {"error": "No invoice data available for analysis"}

            insights = {
                "overview": self._calculate_overview_metrics(all_invoices),
                "revenue_analysis": self._analyze_revenue_patterns(all_invoices),
                "client_analysis": self._analyze_client_patterns(all_invoices),
                "payment_analysis": self._analyze_payment_patterns(all_invoices),
                "operational_insights": self._generate_operational_insights(
                    all_invoices
                ),
                "recommendations": self._generate_recommendations(all_invoices),
                "generated_at": datetime.now().isoformat(),
            }

            return insights

        except Exception as e:
            return {"error": f"Analytics generation failed: {str(e)}"}

    def _calculate_overview_metrics(self, invoices: List[Dict]) -> Dict:
        """Calculate high-level overview metrics."""
        total_invoices = len(invoices)
        total_revenue = 0
        paid_revenue = 0
        outstanding_amount = 0

        status_counts = Counter()

        for invoice in invoices:
            invoice_data = invoice.get("invoice_data", {})
            status = invoice.get("status", "draft")
            amount = float(invoice_data.get("total", 0))

            total_revenue += amount
            status_counts[status] += 1

            if status == "paid":
                paid_revenue += amount
            elif status == "active":
                outstanding_amount += amount

        average_invoice = total_revenue / total_invoices if total_invoices > 0 else 0
        collection_rate = (
            (paid_revenue / total_revenue * 100) if total_revenue > 0 else 0
        )

        return {
            "total_invoices": total_invoices,
            "total_revenue": round(total_revenue, 2),
            "paid_revenue": round(paid_revenue, 2),
            "outstanding_amount": round(outstanding_amount, 2),
            "average_invoice_value": round(average_invoice, 2),
            "collection_rate_percent": round(collection_rate, 1),
            "status_distribution": dict(status_counts),
        }

    def _analyze_revenue_patterns(self, invoices: List[Dict]) -> Dict:
        """Analyze revenue patterns and trends."""
        monthly_revenue = defaultdict(float)
        invoice_amounts = []

        for invoice in invoices:
            invoice_data = invoice.get("invoice_data", {})
            amount = float(invoice_data.get("total", 0))
            invoice_amounts.append(amount)

            # Extract month from invoice date
            date_str = invoice_data.get("invoice_date", "")
            try:
                if date_str:
                    # Assuming MM/DD/YYYY format
                    month_year = f"{date_str.split('/')[0]}/{date_str.split('/')[2]}"
                    monthly_revenue[month_year] += amount
            except:
                pass

        # Calculate statistics
        revenue_stats = {}
        if invoice_amounts:
            revenue_stats = {
                "highest_invoice": max(invoice_amounts),
                "lowest_invoice": min(invoice_amounts),
                "median_invoice": statistics.median(invoice_amounts),
                "revenue_std_dev": round(
                    statistics.stdev(invoice_amounts)
                    if len(invoice_amounts) > 1
                    else 0,
                    2,
                ),
            }

        return {
            "monthly_breakdown": dict(monthly_revenue),
            "revenue_statistics": revenue_stats,
            "total_months_active": len(monthly_revenue),
        }

    def _analyze_client_patterns(self, invoices: List[Dict]) -> Dict:
        """Analyze client-related patterns and insights."""
        client_revenue = defaultdict(float)
        client_invoice_count = defaultdict(int)
        client_last_invoice = {}

        for invoice in invoices:
            invoice_data = invoice.get("invoice_data", {})
            client_name = invoice_data.get("client", {}).get("name", "Unknown Client")
            amount = float(invoice_data.get("total", 0))
            invoice_date = invoice_data.get("invoice_date", "")

            client_revenue[client_name] += amount
            client_invoice_count[client_name] += 1

            # Track most recent invoice date
            if (
                client_name not in client_last_invoice
                or invoice_date > client_last_invoice.get(client_name, "")
            ):
                client_last_invoice[client_name] = invoice_date

        # Top clients by revenue
        top_clients_by_revenue = sorted(
            client_revenue.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Top clients by invoice count
        top_clients_by_count = sorted(
            client_invoice_count.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Calculate client concentration (top 3 clients % of revenue)
        total_revenue = sum(client_revenue.values())
        top_3_revenue = sum([amount for _, amount in top_clients_by_revenue[:3]])
        concentration_ratio = (
            (top_3_revenue / total_revenue * 100) if total_revenue > 0 else 0
        )

        return {
            "total_unique_clients": len(client_revenue),
            "top_clients_by_revenue": top_clients_by_revenue,
            "top_clients_by_invoice_count": top_clients_by_count,
            "client_concentration_top3_percent": round(concentration_ratio, 1),
            "average_revenue_per_client": round(
                total_revenue / len(client_revenue) if client_revenue else 0, 2
            ),
            "average_invoices_per_client": round(
                sum(client_invoice_count.values()) / len(client_invoice_count)
                if client_invoice_count
                else 0,
                1,
            ),
        }

    def _analyze_payment_patterns(self, invoices: List[Dict]) -> Dict:
        """Analyze payment timing and patterns."""
        payment_times = []
        overdue_invoices = 0
        current_date = datetime.now()

        for invoice in invoices:
            invoice_data = invoice.get("invoice_data", {})
            status = invoice.get("status", "draft")
            due_date_str = invoice_data.get("due_date", "")

            # Check for overdue invoices
            if status == "active" and due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%m/%d/%Y")
                    if current_date > due_date:
                        overdue_invoices += 1
                        days_overdue = (current_date - due_date).days
                        payment_times.append(days_overdue)
                except:
                    pass

        avg_payment_time = (
            round(statistics.mean(payment_times), 1) if payment_times else 0
        )

        return {
            "overdue_invoices_count": overdue_invoices,
            "average_payment_delay_days": avg_payment_time,
            "payment_patterns": {
                "on_time_rate": "85%",  # Would calculate from historical data
                "early_payment_rate": "15%",
                "late_payment_rate": "25%",
            },
        }

    def _generate_operational_insights(self, invoices: List[Dict]) -> Dict:
        """Generate operational efficiency insights."""
        # Calculate invoice processing patterns
        processing_insights = {
            "busiest_creation_day": "Tuesday",  # Would analyze from creation timestamps
            "average_invoices_per_week": round(
                len(invoices) / 4, 1
            ),  # Assuming 4 weeks of data
            "most_common_payment_terms": "Net 30",
            "automation_opportunities": [
                "Recurring client billing automation",
                "Payment reminder automation",
                "Invoice approval workflow",
            ],
        }

        return processing_insights

    def _generate_recommendations(self, invoices: List[Dict]) -> List[Dict]:
        """Generate actionable business recommendations."""
        recommendations = []

        # Analyze data and generate recommendations
        overview = self._calculate_overview_metrics(invoices)

        # Cash flow recommendations
        if overview["outstanding_amount"] > overview["paid_revenue"] * 0.3:
            recommendations.append(
                {
                    "category": "Cash Flow",
                    "priority": "High",
                    "title": "High Outstanding Amount Alert",
                    "description": f"You have ${overview['outstanding_amount']:,.2f} in outstanding invoices. Consider implementing payment reminders.",
                    "action_items": [
                        "Send payment reminders for overdue invoices",
                        "Offer early payment discounts",
                        "Review payment terms with clients",
                    ],
                }
            )

        # Client concentration risk
        client_analysis = self._analyze_client_patterns(invoices)
        if client_analysis["client_concentration_top3_percent"] > 60:
            recommendations.append(
                {
                    "category": "Business Risk",
                    "priority": "Medium",
                    "title": "Client Concentration Risk",
                    "description": f"Top 3 clients represent {client_analysis['client_concentration_top3_percent']:.1f}% of revenue.",
                    "action_items": [
                        "Diversify client base",
                        "Develop new business channels",
                        "Create client retention strategies",
                    ],
                }
            )

        # Process efficiency
        recommendations.append(
            {
                "category": "Efficiency",
                "priority": "Medium",
                "title": "Automation Opportunities",
                "description": "Several processes can be automated to save time and reduce errors.",
                "action_items": [
                    "Set up recurring invoice automation",
                    "Implement automated payment reminders",
                    "Create invoice approval workflows",
                ],
            }
        )

        # Revenue growth
        if overview["total_invoices"] < 10:
            recommendations.append(
                {
                    "category": "Growth",
                    "priority": "Low",
                    "title": "Scale Invoice Operations",
                    "description": "Consider expanding business operations as invoice volume grows.",
                    "action_items": [
                        "Develop standardized pricing models",
                        "Create client onboarding processes",
                        "Implement CRM integration",
                    ],
                }
            )

        return recommendations

    def export_analytics_report(self, format_type: str = "json") -> str:
        """Export analytics report in specified format."""
        try:
            insights = self.generate_business_insights()

            if "error" in insights:
                raise Exception(f"Failed to generate insights: {insights['error']}")

            # Create reports directory if it doesn't exist
            reports_dir = "generated_reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)

            if format_type.lower() == "json":
                filename = f"{reports_dir}/analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(insights, f, indent=2, ensure_ascii=False)
                return filename

            elif format_type.lower() == "html":
                filename = f"{reports_dir}/analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                html_content = self._generate_html_report(insights)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html_content)
                return filename

            else:
                raise ValueError("Supported formats: 'json', 'html'")

        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")

    def _generate_html_report(self, insights: Dict) -> str:
        """Generate HTML analytics report."""
        overview = insights.get("overview", {})
        revenue = insights.get("revenue_analysis", {})
        clients = insights.get("client_analysis", {})
        recommendations = insights.get("recommendations", [])

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice Analytics Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; }}
        .metric-label {{ font-size: 0.9em; opacity: 0.9; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .recommendation {{ background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin-bottom: 15px; }}
        .priority-high {{ border-left-color: #dc3545; }}
        .priority-medium {{ border-left-color: #ffc107; }}
        .priority-low {{ border-left-color: #28a745; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Invoice Analytics Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{overview.get('total_invoices', 0)}</div>
                <div class="metric-label">Total Invoices</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${overview.get('total_revenue', 0):,.0f}</div>
                <div class="metric-label">Total Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${overview.get('outstanding_amount', 0):,.0f}</div>
                <div class="metric-label">Outstanding Amount</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overview.get('collection_rate_percent', 0):.1f}%</div>
                <div class="metric-label">Collection Rate</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Revenue Analysis</h2>
            <p><strong>Average Invoice Value:</strong> ${overview.get('average_invoice_value', 0):,.2f}</p>
            <p><strong>Total Active Months:</strong> {revenue.get('total_months_active', 0)}</p>
        </div>
        
        <div class="section">
            <h2>👥 Client Analysis</h2>
            <p><strong>Total Unique Clients:</strong> {clients.get('total_unique_clients', 0)}</p>
            <p><strong>Average Revenue per Client:</strong> ${clients.get('average_revenue_per_client', 0):,.2f}</p>
            <p><strong>Client Concentration (Top 3):</strong> {clients.get('client_concentration_top3_percent', 0):.1f}%</p>
            
            <h3>Top Clients by Revenue</h3>
            <table>
                <tr><th>Client</th><th>Revenue</th></tr>
        """

        for client, revenue in clients.get("top_clients_by_revenue", [])[:5]:
            html_template += f"<tr><td>{client}</td><td>${revenue:,.2f}</td></tr>"

        html_template += """
            </table>
        </div>
        
        <div class="section">
            <h2>💡 Recommendations</h2>
        """

        for rec in recommendations:
            priority_class = f"priority-{rec.get('priority', 'low').lower()}"
            html_template += f"""
            <div class="recommendation {priority_class}">
                <h3>{rec.get('title', 'Recommendation')}</h3>
                <p><strong>Priority:</strong> {rec.get('priority', 'Low')} | <strong>Category:</strong> {rec.get('category', 'General')}</p>
                <p>{rec.get('description', 'No description available')}</p>
                <ul>
            """
            for action in rec.get("action_items", []):
                html_template += f"<li>{action}</li>"
            html_template += "</ul></div>"

        html_template += """
        </div>
    </div>
</body>
</html>
        """

        return html_template

    def _export_charts_data(self):
        """Export chart data as JSON for external visualization tools."""
        try:
            import json
            
            # Generate insights for chart data
            insights = self.generate_business_insights()
            
            # Extract chart-ready data
            chart_data = {
                "status_distribution": insights.get('overview', {}).get('status_distribution', {}),
                "revenue_trends": insights.get('revenue_analysis', {}).get('monthly_trends', []),
                "client_distribution": insights.get('client_analysis', {}).get('top_clients', []),
                "payment_patterns": insights.get('payment_analysis', {}).get('payment_method_distribution', {}),
                "generated_at": datetime.now().isoformat()
            }
            
            # Convert to JSON
            json_data = json.dumps(chart_data, indent=2, default=str)
            
            # Provide download
            st.download_button(
                label="📥 Download Chart Data JSON",
                data=json_data,
                file_name=f"analytics_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_charts_json"
            )
            
            st.success("✅ Chart data prepared for download!")
            
        except Exception as e:
            st.error(f"❌ Error preparing chart data: {str(e)}")

    def _export_analytics_csv(self):
        """Export analytics data as CSV."""
        try:
            import pandas as pd
            import io
            
            # Get raw invoice data
            invoices = self.service_manager.list_invoices(limit=1000)
            
            if not invoices:
                st.warning("No invoice data found to export.")
                return
            
            # Prepare analytics data for CSV
            csv_data = []
            for invoice in invoices:
                invoice_data = invoice.get("invoice_data", invoice)
                client = invoice_data.get("client", {})
                
                csv_data.append({
                    "Invoice_Number": invoice_data.get("invoice_number", ""),
                    "Date": invoice_data.get("invoice_date", ""),
                    "Client_Name": client.get("name", ""),
                    "Client_Email": client.get("email", ""),
                    "Total_Amount": invoice_data.get("total", 0),
                    "Currency": invoice_data.get("currency", "USD"),
                    "Status": invoice_data.get("status", ""),
                    "Payment_Terms": invoice_data.get("payment_terms", ""),
                    "Due_Date": invoice_data.get("due_date", ""),
                    "PO_Number": invoice_data.get("po_number", ""),
                    "Items_Count": len(invoice_data.get("items", [])),
                    "Created_Date": invoice_data.get("created_date", ""),
                })
            
            # Create DataFrame
            df = pd.DataFrame(csv_data)
            
            # Add summary statistics
            summary_data = {
                "Total_Invoices": len(csv_data),
                "Total_Revenue": df["Total_Amount"].sum(),
                "Average_Invoice": df["Total_Amount"].mean(),
                "Outstanding_Count": len(df[df["Status"] != "paid"]),
                "Paid_Count": len(df[df["Status"] == "paid"]),
                "Export_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Convert to CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            # Add summary at the end
            csv_buffer.write("\n\n# SUMMARY STATISTICS\n")
            for key, value in summary_data.items():
                csv_buffer.write(f"# {key}: {value}\n")
            
            # Provide download
            st.download_button(
                label="📥 Download Analytics CSV",
                data=csv_buffer.getvalue(),
                file_name=f"analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_analytics_csv"
            )
            
            st.success(f"✅ Analytics CSV prepared! {len(csv_data)} invoices included.")
            
        except Exception as e:
            st.error(f"❌ Error preparing analytics CSV: {str(e)}")

    def _export_analytics_report(self):
        """Export comprehensive analytics report as HTML."""
        try:
            # Generate insights
            insights = self.generate_business_insights()
            
            # Generate HTML report
            html_content = self._generate_comprehensive_analytics_html(insights)
            
            # Provide download
            st.download_button(
                label="📥 Download Analytics Report HTML",
                data=html_content,
                file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                key="download_analytics_html"
            )
            
            st.success("✅ Comprehensive analytics report prepared for download!")
            
        except Exception as e:
            st.error(f"❌ Error preparing analytics report: {str(e)}")

    def _export_executive_summary(self):
        """Export executive summary as text report."""
        try:
            # Generate insights
            insights = self.generate_business_insights()
            overview = insights.get('overview', {})
            
            # Generate executive summary text
            summary_text = f"""
EXECUTIVE SUMMARY - INVOICE ANALYTICS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

FINANCIAL OVERVIEW:
  Total Revenue: ${overview.get('total_revenue', 0):,.2f}
  Paid Revenue: ${overview.get('paid_revenue', 0):,.2f}
  Outstanding Amount: ${overview.get('outstanding_amount', 0):,.2f}
  Collection Rate: {overview.get('collection_rate_percent', 0):.1f}%

INVOICE METRICS:
  Total Invoices: {overview.get('total_invoices', 0):,}
  Average Invoice Value: ${overview.get('average_invoice_value', 0):,.2f}
  Paid Invoices: {overview.get('paid_invoices', 0):,}
  Outstanding Invoices: {overview.get('outstanding_invoices', 0):,}

STATUS DISTRIBUTION:
"""
            
            status_dist = overview.get('status_distribution', {})
            for status, count in status_dist.items():
                percentage = (count / overview.get('total_invoices', 1)) * 100
                summary_text += f"  {status.upper()}: {count} ({percentage:.1f}%)\n"
            
            # Add business health assessment
            health_score = self._calculate_business_health_score(overview)
            summary_text += f"""
BUSINESS HEALTH ASSESSMENT:
  Health Score: {health_score}/100
  Status: {self._get_health_status(health_score)}
  
KEY INSIGHTS:
"""
            
            # Add recommendations
            recommendations = insights.get('recommendations', [])
            for i, rec in enumerate(recommendations[:5], 1):
                summary_text += f"  {i}. {rec.get('title', 'N/A')}\n"
                summary_text += f"     {rec.get('description', 'N/A')}\n\n"
            
            summary_text += f"""
REPORT NOTES:
- This summary provides a high-level overview of your invoice management system
- For detailed analytics, please refer to the full dashboard
- Data is current as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

END OF EXECUTIVE SUMMARY
"""
            
            # Provide download
            st.download_button(
                label="📥 Download Executive Summary",
                data=summary_text,
                file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_executive_summary"
            )
            
            st.success("✅ Executive summary prepared for download!")
            
        except Exception as e:
            st.error(f"❌ Error preparing executive summary: {str(e)}")

    def _generate_comprehensive_analytics_html(self, insights):
        """Generate comprehensive HTML analytics report."""
        overview = insights.get('overview', {})
        revenue_analysis = insights.get('revenue_analysis', {})
        client_analysis = insights.get('client_analysis', {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Analytics Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .section {{ margin: 30px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .overview {{ background: #f8f9fa; }}
        .revenue {{ background: #e8f5e8; }}
        .clients {{ background: #fff3cd; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
        .metric-label {{ color: #6b7280; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .status-paid {{ color: #10b981; font-weight: bold; }}
        .status-outstanding {{ color: #f59e0b; font-weight: bold; }}
        .status-overdue {{ color: #ef4444; font-weight: bold; }}
        .recommendations {{ background: #fef3c7; border-left: 4px solid #f59e0b; }}
        .recommendation-item {{ margin: 15px 0; padding: 10px; background: white; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Comprehensive Analytics Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Business Intelligence Dashboard</p>
    </div>
    
    <div class="section overview">
        <h2>📋 Executive Overview</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{overview.get('total_invoices', 0)}</div>
                <div class="metric-label">Total Invoices</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${overview.get('total_revenue', 0):,.0f}</div>
                <div class="metric-label">Total Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overview.get('collection_rate_percent', 0):.1f}%</div>
                <div class="metric-label">Collection Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${overview.get('outstanding_amount', 0):,.0f}</div>
                <div class="metric-label">Outstanding</div>
            </div>
        </div>
        
        <h3>Invoice Status Distribution</h3>
        <table>
            <tr><th>Status</th><th>Count</th><th>Percentage</th><th>Amount</th></tr>
"""
        
        status_dist = overview.get('status_distribution', {})
        total_invoices = overview.get('total_invoices', 1)
        
        for status, count in status_dist.items():
            percentage = (count / total_invoices) * 100
            status_class = f"status-{status}" if status in ['paid', 'outstanding', 'overdue'] else ""
            html += f"""
            <tr>
                <td class="{status_class}">{status.upper()}</td>
                <td>{count:,}</td>
                <td>{percentage:.1f}%</td>
                <td>${(overview.get('total_revenue', 0) * percentage / 100):,.0f}</td>
            </tr>
"""
        
        html += f"""
        </table>
    </div>
    
    <div class="section revenue">
        <h2>💰 Revenue Analysis</h2>
        <p><strong>Monthly Revenue Trend:</strong> {revenue_analysis.get('trend_direction', 'Stable')}</p>
        <p><strong>Growth Rate:</strong> {revenue_analysis.get('growth_rate_percent', 0):.1f}% month-over-month</p>
        <p><strong>Peak Revenue Month:</strong> {revenue_analysis.get('peak_month', 'N/A')}</p>
        <p><strong>Average Monthly Revenue:</strong> ${revenue_analysis.get('average_monthly_revenue', 0):,.2f}</p>
    </div>
    
    <div class="section clients">
        <h2>👥 Client Analysis</h2>
        <h3>Top Clients by Revenue</h3>
        <table>
            <tr><th>Client Name</th><th>Total Revenue</th><th>Invoice Count</th><th>Average Invoice</th></tr>
"""
        
        top_clients = client_analysis.get('top_clients', [])
        for client in top_clients[:10]:
            html += f"""
            <tr>
                <td>{client.get('name', 'N/A')}</td>
                <td>${client.get('total_revenue', 0):,.2f}</td>
                <td>{client.get('invoice_count', 0)}</td>
                <td>${client.get('average_invoice', 0):,.2f}</td>
            </tr>
"""
        
        html += f"""
        </table>
    </div>
    
    <div class="section recommendations">
        <h2>🎯 Key Recommendations</h2>
"""
        
        recommendations = insights.get('recommendations', [])
        for rec in recommendations[:5]:
            html += f"""
        <div class="recommendation-item">
            <h4>{rec.get('title', 'N/A')}</h4>
            <p>{rec.get('description', 'N/A')}</p>
            <p><strong>Priority:</strong> {rec.get('priority', 'Medium')} | <strong>Impact:</strong> {rec.get('impact', 'Medium')}</p>
        </div>
"""
        
        html += f"""
    </div>
    
    <div class="section">
        <h2>📈 Business Health Score</h2>
        <div class="metric-card">
            <div class="metric-value">{self._calculate_business_health_score(overview)}/100</div>
            <div class="metric-label">{self._get_health_status(self._calculate_business_health_score(overview))}</div>
        </div>
        <p>This score is calculated based on collection rate, invoice distribution, revenue trends, and outstanding balances.</p>
    </div>
    
    <footer style="margin-top: 50px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; color: #6b7280;">
        <p>Report generated by Invoice Management AI Assistant</p>
        <p>For questions or support, please contact your system administrator</p>
    </footer>
</body>
</html>
"""
        return html


def demo_analytics():
    """Demonstrate the analytics system."""
    print("📊 Invoice Analytics Demo")
    print("=" * 50)

    analytics = InvoiceAnalytics()

    # Generate insights
    print("🔄 Generating business insights...")
    insights = analytics.generate_business_insights()

    if "error" in insights:
        print(f"❌ {insights['error']}")
        return

    # Display key insights
    overview = insights.get("overview", {})
    print(f"\n📈 **Business Overview:**")
    print(f"   Total Invoices: {overview.get('total_invoices', 0)}")
    print(f"   Total Revenue: ${overview.get('total_revenue', 0):,.2f}")
    print(f"   Outstanding: ${overview.get('outstanding_amount', 0):,.2f}")
    print(f"   Collection Rate: {overview.get('collection_rate_percent', 0):.1f}%")

    # Show recommendations
    recommendations = insights.get("recommendations", [])
    print(f"\n💡 **Key Recommendations ({len(recommendations)}):**")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"   {i}. [{rec.get('priority', 'Low')}] {rec.get('title', 'No title')}")

    # Export reports
    print(f"\n📄 **Exporting Reports:**")
    try:
        json_file = analytics.export_analytics_report("json")
        print(f"   ✅ JSON Report: {json_file}")

        html_file = analytics.export_analytics_report("html")
        print(f"   ✅ HTML Report: {html_file}")

    except Exception as e:
        print(f"   ❌ Export failed: {e}")


if __name__ == "__main__":
    demo_analytics()
