import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import sys

# Ensure the root directory is in sys.path so 'from evaluation...' works
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.config import DB_PATH

st.set_page_config(page_title="Agent Evaluation Dashboard", layout="wide")

st.title("📊 Agentic AI Evaluation Dashboard")

@st.cache_data(ttl=5)
def load_data():
    if not os.path.exists(DB_PATH):
        return None, None
        
    conn = sqlite3.connect(DB_PATH)
    runs_df = pd.read_sql_query("SELECT * FROM evaluation_runs ORDER BY id DESC", conn)
    results_df = pd.read_sql_query("SELECT * FROM evaluation_results ORDER BY id DESC", conn)
    conn.close()
    return runs_df, results_df

runs_df, results_df = load_data()

if runs_df is None or runs_df.empty:
    st.info("No evaluation runs yet. Run `python -m evaluation.runner` to generate metrics.")
    st.stop()

# Select Run
latest_run = runs_df.iloc[0]['id']
selected_run = st.sidebar.selectbox("Select Evaluation Run", runs_df['id'].tolist(), index=0)

run_results = results_df[results_df['run_id'] == selected_run]

# Calculate aggregate metrics
total_cases = len(run_results)
e2e_success = run_results['task_success'].mean() * 100
plan_success = run_results['planning_success'].mean() * 100
book_success = run_results['booking_success'].mean() * 100

req_sat = run_results['requirement_satisfaction'].mean()
con_sat = run_results['constraint_satisfaction'].mean()

tool_acc = run_results['tool_selection_accuracy'].mean()
tool_suc = run_results['tool_execution_success'].mean()

consent = run_results['consent_compliance'].mean()
ticket_acc = run_results['ticket_accuracy'].mean()

avg_steps = run_results['total_steps'].mean()
avg_latency = run_results['latency'].mean()
avg_cost = run_results['estimated_cost'].mean() if not pd.isna(run_results['estimated_cost'].mean()) else 0.0

st.header("Executive Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("End-to-End Success", f"{e2e_success:.1f}%")
col2.metric("Planning Success", f"{plan_success:.1f}%")
col3.metric("Booking Success", f"{book_success:.1f}%")
col4.metric("Requirement Satisfaction", f"{req_sat:.1f}%")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Constraint Satisfaction", f"{con_sat:.1f}%")
col6.metric("MCP Tool Accuracy", f"{tool_acc:.1f}%")
col7.metric("Tool Execution Success", f"{tool_suc:.1f}%")
col8.metric("Consent Compliance", f"{consent:.1f}%")

col9, col10, col11, col12 = st.columns(4)
col9.metric("Ticket Accuracy", f"{ticket_acc:.1f}%")
col10.metric("Average Steps", f"{avg_steps:.1f}")
col11.metric("Average Latency", f"{avg_latency:.1f} s")
col12.metric("Average Cost", f"${avg_cost:.4f}" if avg_cost > 0 else "N/A")


st.divider()

st.header("Failure Distribution")
failures = run_results[run_results['task_success'] == 0]['failure_category'].value_counts()
if not failures.empty:
    st.bar_chart(failures)
else:
    st.success("No failures in this run!")

st.header("Test Case Details")
display_df = run_results[['test_case_id', 'query', 'task_success', 'planning_success', 'booking_success', 'requirement_satisfaction', 'tool_selection_accuracy', 'latency']]
st.dataframe(display_df, use_container_width=True)

st.header("Deep Dive")
selected_test = st.selectbox("Select Test Case for deep dive", run_results['test_case_id'].tolist())

if selected_test:
    test_data = run_results[run_results['test_case_id'] == selected_test].iloc[0]
    
    st.subheader(f"Query: {test_data['query']}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Expected Request**")
        st.write(test_data['query'])
        
    with c2:
        st.write("**Failure Analysis**")
        st.write(f"Category: {test_data['failure_category']}")
        st.write(f"Reason: {test_data['failure_reason']}")
        
    st.write("**Agent Trace**")
    try:
        trace = json.loads(test_data['raw_trace'])
        for step in trace.get("steps", []):
            st.write(f"✅ Agent Node: **{step.get('name')}** (Latency: {step.get('latency', 0):.2f}s)")
        for tool in trace.get("tools", []):
            status = "✅" if tool.get("success") else "❌"
            st.write(f"{status} MCP Tool: **{tool.get('tool_name')}** (Latency: {tool.get('latency', 0):.2f}s)")
            with st.expander("Tool Arguments"):
                st.json(tool.get("arguments", {}))
    except Exception as e:
        st.error(f"Could not parse trace: {e}")
