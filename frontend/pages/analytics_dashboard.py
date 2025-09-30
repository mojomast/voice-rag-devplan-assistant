import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = st.secrets.get("API_URL", "http://localhost:8000")

def render_analytics_dashboard():
    st.set_page_config(
        page_title="📊 Voice RAG Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("📊 Voice RAG Analytics Dashboard")
    st.markdown("**Real-time monitoring and analytics for the Voice-Enabled RAG System**")

    # Auto-refresh controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("### Dashboard Overview")
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
    with col3:
        refresh_interval = st.selectbox("Interval", [5, 10, 30, 60], index=1, format_func=lambda x: f"{x}s")
    with col4:
        if st.button("🔄 Refresh Now") or auto_refresh:
            st.rerun()

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

    # Fetch analytics data
    with st.spinner("📊 Loading analytics data..."):
        try:
            analytics_data = fetch_analytics_data()
        except Exception as e:
            st.error(f"Failed to load analytics data: {e}")
            analytics_data = generate_mock_analytics_data()

    if not analytics_data:
        st.warning("No analytics data available")
        return

    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚀 Performance",
        "💰 Cost Analysis",
        "📈 Usage Stats",
        "🖥️ System Resources",
        "🚨 Health & Alerts",
        "📊 Real-time Metrics"
    ])

    with tab1:
        render_performance_metrics(analytics_data)

    with tab2:
        render_cost_analysis(analytics_data)

    with tab3:
        render_usage_statistics(analytics_data)

    with tab4:
        render_system_resources(analytics_data)

    with tab5:
        render_health_alerts(analytics_data)

    with tab6:
        render_realtime_metrics(analytics_data)

def render_performance_metrics(data: Dict[str, Any]):
    st.header("🚀 System Performance Metrics")

    # Key performance indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_response = data.get("avg_response_time", 0)
        change = data.get("response_time_change", 0)
        st.metric(
            "Avg Response Time",
            f"{avg_response:.2f}s",
            delta=f"{change:.2f}s",
            delta_color="inverse"
        )

    with col2:
        success_rate = data.get("success_rate", 0)
        change = data.get("success_rate_change", 0)
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%",
            delta=f"{change:.1f}%"
        )

    with col3:
        total_queries = data.get("total_queries", 0)
        change = data.get("queries_change", 0)
        st.metric(
            "Total Queries",
            f"{total_queries:,}",
            delta=change
        )

    with col4:
        throughput = data.get("queries_per_second", 0)
        change = data.get("throughput_change", 0)
        st.metric(
            "Throughput",
            f"{throughput:.2f} req/s",
            delta=f"{change:.2f}"
        )

    # Response time trends
    st.subheader("📈 Response Time Trends")
    if "response_times" in data:
        df_response = pd.DataFrame(data["response_times"])
        df_response['timestamp'] = pd.to_datetime(df_response['timestamp'])

        fig = px.line(
            df_response,
            x="timestamp",
            y="response_time",
            title="Response Time Over Time",
            labels={"response_time": "Response Time (s)", "timestamp": "Time"}
        )
        fig.update_layout(height=400, showlegend=False)
        fig.add_hline(y=df_response['response_time'].mean(), line_dash="dash",
                     annotation_text=f"Average: {df_response['response_time'].mean():.2f}s")
        st.plotly_chart(fig, use_container_width=True)

    # Endpoint performance breakdown
    st.subheader("🎯 Endpoint Performance")
    if "endpoint_stats" in data:
        endpoint_data = data["endpoint_stats"]

        col1, col2 = st.columns(2)

        with col1:
            # Average response times
            endpoints = list(endpoint_data.keys())
            avg_times = [endpoint_data[ep].get("avg_response_time", 0) for ep in endpoints]

            fig_times = px.bar(
                x=endpoints,
                y=avg_times,
                title="Average Response Time by Endpoint",
                labels={"x": "Endpoint", "y": "Avg Response Time (s)"},
                color=avg_times,
                color_continuous_scale="Viridis"
            )
            fig_times.update_layout(height=400)
            st.plotly_chart(fig_times, use_container_width=True)

        with col2:
            # Success rates
            success_rates = [endpoint_data[ep].get("success_rate", 0) for ep in endpoints]

            fig_success = px.bar(
                x=endpoints,
                y=success_rates,
                title="Success Rate by Endpoint",
                labels={"x": "Endpoint", "y": "Success Rate (%)"},
                color=success_rates,
                color_continuous_scale="RdYlGn"
            )
            fig_success.update_layout(height=400)
            st.plotly_chart(fig_success, use_container_width=True)

    # Performance insights
    st.subheader("💡 Performance Insights")
    insights = []

    if data.get("avg_response_time", 0) > 2.0:
        insights.append("⚠️ Average response time is above 2 seconds - consider optimization")

    if data.get("success_rate", 100) < 95:
        insights.append("🚨 Success rate below 95% - investigate error patterns")

    if data.get("queries_per_second", 0) > 10:
        insights.append("🔥 High throughput detected - monitor resource usage")

    if not insights:
        insights.append("✅ All performance metrics are within normal ranges")

    for insight in insights:
        st.markdown(f"- {insight}")

def render_cost_analysis(data: Dict[str, Any]):
    st.header("💰 Cost Analysis & Optimization")

    cost_data = data.get("cost_analysis", {})

    # Cost overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_cost = cost_data.get("total_cost", 0)
        st.metric("Total Cost (7 days)", f"${total_cost:.4f}")

    with col2:
        daily_avg = cost_data.get("daily_average", 0)
        st.metric("Daily Average", f"${daily_avg:.4f}")

    with col3:
        monthly_proj = cost_data.get("monthly_projection", 0)
        st.metric("Monthly Projection", f"${monthly_proj:.2f}")

    with col4:
        total_calls = cost_data.get("total_calls", 0)
        st.metric("Total API Calls", f"{total_calls:,}")

    # Cost breakdown by model
    if "cost_by_model" in cost_data:
        st.subheader("📊 Cost Distribution by Model")

        model_data = cost_data["cost_by_model"]

        # Prepare data for visualization
        models = list(model_data.keys())
        costs = [model_data[model]["cost"] for model in models]
        calls = [model_data[model]["calls"] for model in models]

        col1, col2 = st.columns(2)

        with col1:
            # Cost distribution pie chart
            fig_pie = px.pie(
                values=costs,
                names=models,
                title="Cost Distribution by Model",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # API calls bar chart
            fig_calls = px.bar(
                x=models,
                y=calls,
                title="API Calls by Model",
                labels={"x": "Model", "y": "Number of Calls"},
                color=calls,
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_calls, use_container_width=True)

        # Detailed model breakdown table
        st.subheader("📋 Detailed Model Breakdown")
        model_df = pd.DataFrame([
            {
                "Model": model,
                "Calls": data["calls"],
                "Cost": f"${data['cost']:.6f}",
                "Avg Cost/Call": f"${data['cost']/data['calls']:.8f}" if data['calls'] > 0 else "$0.00",
                "Tokens": data.get('tokens', 0),
                "Characters": data.get('characters', 0)
            }
            for model, data in model_data.items()
        ])
        st.dataframe(model_df, use_container_width=True)

    # Daily cost trends
    if "daily_costs" in cost_data:
        st.subheader("📈 Daily Cost Trends")
        df_costs = pd.DataFrame(cost_data["daily_costs"])
        df_costs['date'] = pd.to_datetime(df_costs['date'])

        fig_trend = px.line(
            df_costs,
            x="date",
            y="cost",
            title="Daily API Costs",
            labels={"cost": "Cost ($)", "date": "Date"}
        )
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, use_container_width=True)

    # Cost optimization recommendations
    st.subheader("💡 Cost Optimization Recommendations")
    recommendations = []

    # Calculate percentage of each model
    if "cost_by_model" in cost_data:
        total_cost = sum(model_data[model]["cost"] for model in model_data)
        for model, data in model_data.items():
            percentage = (data["cost"] / total_cost * 100) if total_cost > 0 else 0
            if percentage > 50 and "gpt-4" in model.lower():
                recommendations.append(f"🔄 Consider using cheaper models for {percentage:.1f}% of {model} usage")
            if data["calls"] > 1000 and "embedding" not in model.lower():
                recommendations.append(f"💾 Implement caching for {model} to reduce API calls")

    if monthly_proj > 100:
        recommendations.append("📊 Monthly projection exceeds $100 - consider implementing Requesty.ai routing")

    if not recommendations:
        recommendations.append("✅ Cost optimization is on track")

    for rec in recommendations:
        st.markdown(f"- {rec}")

def render_usage_statistics(data: Dict[str, Any]):
    st.header("📈 Usage Statistics & Patterns")

    usage_data = data.get("usage_stats", {})

    # Usage overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        docs_processed = usage_data.get("documents_processed", 0)
        st.metric("Documents Processed", docs_processed)

    with col2:
        voice_queries = usage_data.get("voice_queries", 0)
        st.metric("Voice Queries", voice_queries)

    with col3:
        text_queries = usage_data.get("text_queries", 0)
        st.metric("Text Queries", text_queries)

    with col4:
        total_queries = voice_queries + text_queries
        st.metric("Total Queries", total_queries)

    # Query type distribution
    if voice_queries > 0 or text_queries > 0:
        st.subheader("📊 Query Type Distribution")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            fig_dist = px.pie(
                values=[voice_queries, text_queries],
                names=["Voice Queries", "Text Queries"],
                title="Query Type Distribution",
                color_discrete_sequence=["#FF6B6B", "#4ECDC4"]
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        with col2:
            # Bar chart with percentages
            total = voice_queries + text_queries
            voice_pct = (voice_queries / total * 100) if total > 0 else 0
            text_pct = (text_queries / total * 100) if total > 0 else 0

            fig_bar = px.bar(
                x=["Voice", "Text"],
                y=[voice_pct, text_pct],
                title="Query Type Percentage",
                labels={"x": "Query Type", "y": "Percentage (%)"},
                color=["Voice", "Text"],
                color_discrete_map={"Voice": "#FF6B6B", "Text": "#4ECDC4"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # User activity heatmap
    if "hourly_activity" in usage_data:
        st.subheader("🔥 User Activity Heatmap")

        activity_data = usage_data["hourly_activity"]

        # Create sample heatmap data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = list(range(24))

        # Generate sample data if not provided
        if isinstance(activity_data, dict):
            heatmap_data = np.random.poisson(5, (7, 24))  # Sample data
        else:
            heatmap_data = np.array(activity_data)

        fig_heatmap = px.imshow(
            heatmap_data,
            x=hours,
            y=days,
            title="User Activity by Hour and Day",
            labels={"x": "Hour of Day", "y": "Day of Week", "color": "Query Count"},
            color_continuous_scale="Viridis"
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # Usage insights
    st.subheader("💡 Usage Insights")

    total_queries = voice_queries + text_queries
    if total_queries > 0:
        voice_percentage = (voice_queries / total_queries * 100)

        insights = []
        if voice_percentage > 60:
            insights.append("🎤 Voice queries dominate usage - ensure voice infrastructure is optimized")
        elif voice_percentage < 20:
            insights.append("📝 Text queries are preferred - consider improving voice UX")
        else:
            insights.append("⚖️ Balanced usage between voice and text queries")

        if docs_processed < 10:
            insights.append("📄 Low document count - encourage users to upload more content")

        if total_queries > 1000:
            insights.append("🚀 High query volume - monitor system performance")

        for insight in insights:
            st.markdown(f"- {insight}")

def render_system_resources(data: Dict[str, Any]):
    st.header("🖥️ System Resources & Infrastructure")

    system_data = data.get("system_metrics", {})

    if not system_data:
        st.warning("No system metrics available")
        return

    # Current resource usage
    current_metrics = system_data.get("current", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cpu_usage = current_metrics.get("cpu_percent", 0)
        st.metric("CPU Usage", f"{cpu_usage:.1f}%")

        # CPU usage gauge
        fig_cpu = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cpu_usage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CPU %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_cpu.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_cpu, use_container_width=True)

    with col2:
        memory_usage = current_metrics.get("memory_percent", 0)
        st.metric("Memory Usage", f"{memory_usage:.1f}%")

        # Memory gauge
        fig_mem = go.Figure(go.Indicator(
            mode="gauge+number",
            value=memory_usage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Memory %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ]
            }
        ))
        fig_mem.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_mem, use_container_width=True)

    with col3:
        disk_usage = current_metrics.get("disk_percent", 0)
        st.metric("Disk Usage", f"{disk_usage:.1f}%")

        # Disk gauge
        fig_disk = go.Figure(go.Indicator(
            mode="gauge+number",
            value=disk_usage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Disk %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "orange"},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "red"}
                ]
            }
        ))
        fig_disk.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_disk, use_container_width=True)

    with col4:
        network_io = current_metrics.get("network_io", 0)
        st.metric("Network I/O", f"{network_io:.2f} MB/s")

        # Network activity bar
        fig_net = go.Figure(go.Bar(
            x=["Network I/O"],
            y=[network_io],
            marker_color="purple"
        ))
        fig_net.update_layout(
            height=250,
            title="Network Activity",
            yaxis_title="MB/s",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_net, use_container_width=True)

    # Historical trends
    if "historical" in system_data:
        st.subheader("📊 Resource Usage Trends")

        historical = system_data["historical"]
        if historical:
            df_hist = pd.DataFrame(historical)
            df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'])

            fig_trends = go.Figure()

            fig_trends.add_trace(go.Scatter(
                x=df_hist["timestamp"],
                y=df_hist["cpu_percent"],
                name="CPU %",
                line=dict(color='blue')
            ))
            fig_trends.add_trace(go.Scatter(
                x=df_hist["timestamp"],
                y=df_hist["memory_percent"],
                name="Memory %",
                line=dict(color='green')
            ))
            fig_trends.add_trace(go.Scatter(
                x=df_hist["timestamp"],
                y=df_hist["disk_percent"],
                name="Disk %",
                line=dict(color='orange')
            ))

            fig_trends.update_layout(
                title="System Resource Usage Over Time",
                xaxis_title="Time",
                yaxis_title="Usage %",
                height=400
            )
            st.plotly_chart(fig_trends, use_container_width=True)

    # Resource alerts
    st.subheader("⚠️ Resource Alerts")

    alerts = []
    if cpu_usage > 80:
        alerts.append(f"🔴 HIGH: CPU usage at {cpu_usage:.1f}%")
    elif cpu_usage > 60:
        alerts.append(f"🟡 MEDIUM: CPU usage at {cpu_usage:.1f}%")

    if memory_usage > 85:
        alerts.append(f"🔴 HIGH: Memory usage at {memory_usage:.1f}%")
    elif memory_usage > 70:
        alerts.append(f"🟡 MEDIUM: Memory usage at {memory_usage:.1f}%")

    if disk_usage > 85:
        alerts.append(f"🔴 HIGH: Disk usage at {disk_usage:.1f}%")
    elif disk_usage > 70:
        alerts.append(f"🟡 MEDIUM: Disk usage at {disk_usage:.1f}%")

    if not alerts:
        alerts.append("✅ All resource usage within normal limits")

    for alert in alerts:
        if "HIGH" in alert:
            st.error(alert)
        elif "MEDIUM" in alert:
            st.warning(alert)
        else:
            st.success(alert)

def render_health_alerts(data: Dict[str, Any]):
    st.header("🚨 System Health & Alerts")

    health_data = data.get("health_status", {})

    # Overall health status
    col1, col2 = st.columns(2)

    with col1:
        status = health_data.get("status", "unknown")
        health_score = health_data.get("health_score", 0)

        # Health status indicator
        if status == "healthy":
            st.success(f"✅ System Status: {status.upper()}")
        elif status == "degraded":
            st.warning(f"⚠️ System Status: {status.upper()}")
        else:
            st.error(f"❌ System Status: {status.upper()}")

    with col2:
        # Health score gauge
        fig_health = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Health Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "green" if health_score >= 80 else "orange" if health_score >= 60 else "red"},
                'steps': [
                    {'range': [0, 60], 'color': "lightcoral"},
                    {'range': [60, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_health.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_health, use_container_width=True)

    # Health checks
    st.subheader("🔍 Health Checks")
    checks = health_data.get("checks", {})

    col1, col2 = st.columns(2)

    with col1:
        for check_name, check_status in list(checks.items())[:len(checks)//2 + len(checks)%2]:
            display_name = check_name.replace('_', ' ').title()
            if check_status:
                st.success(f"✅ {display_name}")
            else:
                st.error(f"❌ {display_name}")

    with col2:
        for check_name, check_status in list(checks.items())[len(checks)//2 + len(checks)%2:]:
            display_name = check_name.replace('_', ' ').title()
            if check_status:
                st.success(f"✅ {display_name}")
            else:
                st.error(f"❌ {display_name}")

    # Recent alerts
    if "recent_alerts" in data:
        st.subheader("📋 Recent Alerts")
        alerts = data["recent_alerts"]

        if alerts:
            for alert in alerts[-10:]:  # Show last 10 alerts
                timestamp = alert.get("timestamp", "")
                level = alert.get("level", "info")
                message = alert.get("message", "")

                if level == "error":
                    st.error(f"🚨 {timestamp}: {message}")
                elif level == "warning":
                    st.warning(f"⚠️ {timestamp}: {message}")
                else:
                    st.info(f"ℹ️ {timestamp}: {message}")
        else:
            st.info("No recent alerts")

    # Health recommendations
    st.subheader("💡 Health Recommendations")

    recommendations = []

    if health_score < 60:
        recommendations.append("🚨 CRITICAL: Immediate attention required - check failed health checks")
    elif health_score < 80:
        recommendations.append("⚠️ WARNING: System performance degraded - investigate resource usage")

    failed_checks = [check for check, status in checks.items() if not status]
    if failed_checks:
        recommendations.append(f"🔧 Address failed health checks: {', '.join(failed_checks)}")

    if not recommendations:
        recommendations.append("✅ System health is optimal")

    for rec in recommendations:
        if "CRITICAL" in rec:
            st.error(rec)
        elif "WARNING" in rec:
            st.warning(rec)
        else:
            st.success(rec)

def render_realtime_metrics(data: Dict[str, Any]):
    st.header("📊 Real-time Metrics & Live Data")

    # Create containers for live updating metrics
    metrics_container = st.container()
    charts_container = st.container()

    with metrics_container:
        st.subheader("⚡ Live System Metrics")

        # Real-time metrics grid
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric("Requests/sec", f"{data.get('queries_per_second', 0):.2f}")
        with col2:
            st.metric("Avg Latency", f"{data.get('avg_response_time', 0):.2f}s")
        with col3:
            st.metric("Error Rate", f"{100 - data.get('success_rate', 100):.1f}%")
        with col4:
            current_metrics = data.get("system_metrics", {}).get("current", {})
            st.metric("CPU", f"{current_metrics.get('cpu_percent', 0):.1f}%")
        with col5:
            st.metric("Memory", f"{current_metrics.get('memory_percent', 0):.1f}%")
        with col6:
            st.metric("Active Requests", data.get('active_requests_total', 0))

    with charts_container:
        st.subheader("📈 Live Performance Charts")

        # Generate sample real-time data for demonstration
        time_points = pd.date_range(start=datetime.now() - timedelta(minutes=30),
                                  end=datetime.now(), freq='1min')

        col1, col2 = st.columns(2)

        with col1:
            # Real-time response time chart
            response_times = np.random.normal(1.2, 0.3, len(time_points))
            response_times = np.maximum(response_times, 0.1)  # Ensure positive values

            fig_rt = px.line(
                x=time_points,
                y=response_times,
                title="Response Time (Last 30 minutes)",
                labels={"x": "Time", "y": "Response Time (s)"}
            )
            fig_rt.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_rt, use_container_width=True)

        with col2:
            # Real-time throughput chart
            throughput = np.random.poisson(3, len(time_points))

            fig_tp = px.bar(
                x=time_points,
                y=throughput,
                title="Request Throughput (Last 30 minutes)",
                labels={"x": "Time", "y": "Requests/minute"}
            )
            fig_tp.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_tp, use_container_width=True)

    # Live logs section
    st.subheader("📜 Live System Logs")

    # Mock log entries
    log_entries = [
        {"timestamp": "2024-01-15 10:30:45", "level": "INFO", "message": "Voice query processed successfully"},
        {"timestamp": "2024-01-15 10:30:40", "level": "INFO", "message": "Document uploaded and indexed"},
        {"timestamp": "2024-01-15 10:30:35", "level": "WARNING", "message": "High response time detected: 2.1s"},
        {"timestamp": "2024-01-15 10:30:30", "level": "INFO", "message": "RAG query completed"},
        {"timestamp": "2024-01-15 10:30:25", "level": "ERROR", "message": "Transcription failed for audio file"},
    ]

    for entry in log_entries:
        level = entry["level"]
        if level == "ERROR":
            st.error(f"🔴 [{entry['timestamp']}] {entry['message']}")
        elif level == "WARNING":
            st.warning(f"🟡 [{entry['timestamp']}] {entry['message']}")
        else:
            st.info(f"🔵 [{entry['timestamp']}] {entry['message']}")

def fetch_analytics_data() -> Optional[Dict[str, Any]]:
    """Fetch analytics data from backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/dashboard", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.RequestException as e:
        st.warning(f"Connection Error: {e} - Using mock data")
        return generate_mock_analytics_data()

def generate_mock_analytics_data() -> Dict[str, Any]:
    """Generate comprehensive mock analytics data for demonstration"""
    now = datetime.now()

    return {
        # Performance metrics
        "avg_response_time": 1.25,
        "response_time_change": -0.15,
        "success_rate": 98.5,
        "success_rate_change": 1.2,
        "total_queries": 1247,
        "queries_change": 156,
        "queries_per_second": 2.34,
        "throughput_change": 0.45,
        "active_requests_total": 5,

        # Response time history
        "response_times": [
            {
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "response_time": max(0.1, np.random.normal(1.2, 0.3))
            }
            for i in range(24, 0, -1)
        ],

        # Endpoint statistics
        "endpoint_stats": {
            "/query/text": {"avg_response_time": 1.1, "success_rate": 99.2, "total_requests": 450},
            "/query/voice": {"avg_response_time": 2.3, "success_rate": 97.8, "total_requests": 230},
            "/documents/upload": {"avg_response_time": 0.8, "success_rate": 99.5, "total_requests": 120},
            "/voice/transcribe-base64": {"avg_response_time": 1.8, "success_rate": 98.1, "total_requests": 180},
        },

        # Cost analysis
        "cost_analysis": {
            "total_cost": 12.45,
            "daily_average": 1.78,
            "monthly_projection": 53.40,
            "total_calls": 892,
            "cost_by_model": {
                "gpt-4o-mini": {"cost": 8.23, "calls": 567, "tokens": 125000, "characters": 0},
                "text-embedding-3-small": {"cost": 2.15, "calls": 234, "tokens": 78000, "characters": 0},
                "whisper-1": {"cost": 1.85, "calls": 67, "tokens": 0, "characters": 0},
                "tts-1": {"cost": 0.22, "calls": 24, "tokens": 0, "characters": 15000}
            },
            "daily_costs": [
                {"date": (now - timedelta(days=i)).date().isoformat(), "cost": np.random.uniform(1.0, 3.0)}
                for i in range(7, 0, -1)
            ]
        },

        # Usage statistics
        "usage_stats": {
            "documents_processed": 45,
            "voice_queries": 289,
            "text_queries": 634,
            "hourly_activity": np.random.poisson(5, (7, 24)).tolist()
        },

        # System metrics
        "system_metrics": {
            "current": {
                "cpu_percent": 34.5,
                "memory_percent": 68.2,
                "disk_percent": 45.8,
                "network_io": 2.34
            },
            "historical": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "cpu_percent": max(0, min(100, np.random.normal(35, 15))),
                    "memory_percent": max(0, min(100, np.random.normal(65, 10))),
                    "disk_percent": max(0, min(100, np.random.normal(46, 5)))
                }
                for i in range(24, 0, -1)
            ]
        },

        # Health status
        "health_status": {
            "status": "healthy",
            "health_score": 87,
            "checks": {
                "cpu_ok": True,
                "memory_ok": True,
                "disk_ok": True,
                "api_responsive": True,
                "database_connected": True,
                "vector_store_accessible": True
            }
        },

        # Recent alerts
        "recent_alerts": [
            {"timestamp": "2024-01-15 10:25:00", "level": "warning", "message": "High memory usage detected"},
            {"timestamp": "2024-01-15 10:20:00", "level": "info", "message": "System startup completed"},
            {"timestamp": "2024-01-15 10:15:00", "level": "error", "message": "Temporary API rate limit exceeded"},
        ]
    }

if __name__ == "__main__":
    render_analytics_dashboard()