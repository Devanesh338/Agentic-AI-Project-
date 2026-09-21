import sqlite3
import json
import datetime
import random
from evaluation.config import DB_PATH

def insert_mock_run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    total_cases = 10
    
    # Insert run
    cursor.execute(
        "INSERT INTO evaluation_runs (timestamp, total_cases, overall_success_rate) VALUES (?, ?, ?)",
        (timestamp, total_cases, 90.0)
    )
    run_id = cursor.lastrowid
    
    for i in range(total_cases):
        is_success = (i < 9)  # 9 successes, 1 failure
        
        # 90% metrics on average
        test_case_id = f"MOCK_{i+1:03d}"
        query = f"Mocked query for test case {i+1}"
        
        if is_success:
            task_success = True
            planning_success = True
            booking_success = True
            req_sat = 100.0
            con_sat = 100.0
            tool_acc = 100.0
            tool_exec = 100.0
            consent_comp = 100.0
            ticket_acc = 100.0
            failure_category = None
            failure_reason = None
        else:
            task_success = False
            planning_success = False
            booking_success = False
            req_sat = 0.0
            con_sat = 0.0
            tool_acc = 0.0
            tool_exec = 0.0
            consent_comp = 0.0
            ticket_acc = 0.0
            failure_category = "PLANNING_FAILURE"
            failure_reason = "Mocked failure to achieve 90% overall"
            
        trace = {
            "steps": [{"name": "mock_agent", "latency": 2.5}],
            "tools": [{"tool_name": "mock_tool", "latency": 1.2, "success": True}]
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
            run_id, test_case_id, query, task_success, planning_success, booking_success,
            req_sat, con_sat, tool_acc, tool_exec, 0.0, consent_comp,
            0.0, 0.0, 0.0, ticket_acc,
            5.0, 5, 12.5, 8.0, 4.0, 0.5,
            4, 2, 15000, 0.015, 0.0,
            False, False, failure_category, failure_reason, None, None,
            4.5 if is_success else 0.0, "{}", json.dumps(trace), timestamp
        ))
        
    conn.commit()
    conn.close()
    print(f"Successfully inserted mock run (ID: {run_id}) with exactly 90% metrics.")

if __name__ == "__main__":
    insert_mock_run()
