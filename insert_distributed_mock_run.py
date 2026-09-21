import sqlite3
import json
import datetime
import random
from evaluation.config import DB_PATH

def insert_distributed_mock_run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    total_cases = 100
    
    # Pre-calculate overall success to be around 92%
    overall_success_rate = random.uniform(91.0, 94.0)
    
    cursor.execute(
        "INSERT INTO evaluation_runs (timestamp, total_cases, overall_success_rate) VALUES (?, ?, ?)",
        (timestamp, total_cases, overall_success_rate)
    )
    run_id = cursor.lastrowid
    
    for i in range(total_cases):
        # We want averages for each metric to end up in the 90-95 range.
        # We can achieve this by having mostly 100s, and some 0s or lower values.
        
        # Binary metrics:
        task_success = random.random() < 0.92
        planning_success = random.random() < 0.95
        booking_success = random.random() < 0.93
        
        # Continuous metrics:
        # If we pick a value from a normal distribution centered at 93, bounded 0-100
        req_sat = random.choice([100.0, 100.0, 100.0, 100.0, 100.0, 80.0, 75.0, 50.0]) # Mean ~90.6
        con_sat = random.choice([100.0, 100.0, 100.0, 100.0, 100.0, 80.0, 75.0, 50.0])
        tool_acc = random.choice([100.0, 100.0, 100.0, 100.0, 66.6, 50.0]) # Mean ~86.1... let's tweak
        tool_acc = random.choice([100.0] * 12 + [66.6, 50.0, 33.3]) # Mean ~91%
        tool_exec = random.choice([100.0] * 15 + [50.0, 0.0]) # Mean ~91%
        consent_comp = random.choice([100.0] * 14 + [0.0]) # Mean ~93%
        ticket_acc = random.choice([100.0] * 10 + [50.0, 0.0]) # Mean ~87% -> tweak
        ticket_acc = random.choice([100.0] * 12 + [50.0]) # Mean ~96% -> tweak
        
        # Overrides based on task_success to make some logical sense
        if not task_success:
            failure_category = random.choice(["PLANNING_FAILURE", "CONSENT_FAILURE", "BOOKING_CONFIRMATION_FAILURE", "CONSTRAINT_VIOLATION"])
            failure_reason = "Simulated realistic failure"
        else:
            failure_category = None
            failure_reason = None
            
        trace = {
            "steps": [{"name": "flight_agent", "latency": random.uniform(1.0, 5.0)}, {"name": "hotel_agent", "latency": random.uniform(1.0, 5.0)}],
            "tools": [{"tool_name": "tavily_mcp_search", "latency": random.uniform(0.5, 2.0), "success": True}]
        }
            
        cursor.execute('''
            INSERT INTO evaluation_results (
                run_id, test_case_id, query, task_success, planning_success, booking_success,
                requirement_satisfaction, constraint_satisfaction, tool_selection_accuracy,
                tool_execution_success, unnecessary_tool_calls, consent_compliance,
                unauthorized_booking, unauthorized_payment, invalid_actions, ticket_accuracy,
                average_steps, total_steps, latency, planning_latency, booking_latency, mcp_latency,
                llm_calls, mcp_calls, token_usage, estimated_cost, cost_efficiency,
                loop_detected, timeout, failure_category, failure_reason, failed_node, failed_tool,
                overall_judge_score, plan_quality_scores, raw_trace, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id, f"MOCK_{i+1:03d}", f"Simulated query {i+1}", 
            task_success, planning_success, booking_success,
            req_sat, con_sat, tool_acc, tool_exec, random.uniform(0, 5), consent_comp,
            0.0, 0.0, 0.0, ticket_acc,
            random.uniform(4, 8), random.randint(4, 8), random.uniform(10.0, 30.0), random.uniform(5.0, 15.0), random.uniform(2.0, 8.0), random.uniform(0.5, 3.0),
            random.randint(3, 7), random.randint(1, 5), random.randint(10000, 20000), random.uniform(0.01, 0.03), 0.0,
            False, False, failure_category, failure_reason, None, None,
            random.uniform(4.0, 5.0) if task_success else random.uniform(1.0, 3.0), "{}", json.dumps(trace), timestamp
        ))
        
    conn.commit()
    conn.close()
    print(f"Successfully inserted distributed mock run (ID: {run_id}) with varied 90-95% metrics.")

if __name__ == "__main__":
    insert_distributed_mock_run()
