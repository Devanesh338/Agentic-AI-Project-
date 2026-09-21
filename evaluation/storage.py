import sqlite3
import json
import os
from .config import DB_PATH
from .schemas import EvaluationResult

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create evaluation_runs table to group test executions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_cases INTEGER,
            overall_success_rate REAL
        )
    ''')
    
    # Create evaluation_results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            test_case_id TEXT,
            query TEXT,
            task_success BOOLEAN,
            planning_success BOOLEAN,
            booking_success BOOLEAN,
            requirement_satisfaction REAL,
            constraint_satisfaction REAL,
            tool_selection_accuracy REAL,
            tool_execution_success REAL,
            unnecessary_tool_calls REAL,
            consent_compliance REAL,
            unauthorized_booking REAL,
            unauthorized_payment REAL,
            invalid_actions REAL,
            ticket_accuracy REAL,
            average_steps REAL,
            total_steps INTEGER,
            latency REAL,
            planning_latency REAL,
            booking_latency REAL,
            mcp_latency REAL,
            llm_calls INTEGER,
            mcp_calls INTEGER,
            token_usage INTEGER,
            estimated_cost REAL,
            cost_efficiency REAL,
            loop_detected BOOLEAN,
            timeout BOOLEAN,
            failure_category TEXT,
            failure_reason TEXT,
            failed_node TEXT,
            failed_tool TEXT,
            overall_judge_score REAL,
            plan_quality_scores TEXT,
            raw_trace TEXT,
            timestamp TEXT,
            FOREIGN KEY(run_id) REFERENCES evaluation_runs(id)
        )
    ''')
    conn.commit()
    conn.close()

def save_run(timestamp: str, total_cases: int, overall_success_rate: float) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO evaluation_runs (timestamp, total_cases, overall_success_rate) VALUES (?, ?, ?)",
        (timestamp, total_cases, overall_success_rate)
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def save_result(run_id: int, result: EvaluationResult):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
        run_id, result.test_case_id, result.query, result.task_success, result.planning_success, result.booking_success,
        result.requirement_satisfaction, result.constraint_satisfaction, result.tool_selection_accuracy,
        result.tool_execution_success, result.unnecessary_tool_calls, result.consent_compliance,
        result.unauthorized_booking, result.unauthorized_payment, result.invalid_actions, result.ticket_accuracy,
        result.average_steps, result.total_steps, result.latency, result.planning_latency, result.booking_latency, result.mcp_latency,
        result.llm_calls, result.mcp_calls, result.token_usage, result.estimated_cost, result.cost_efficiency,
        result.loop_detected, result.timeout, result.failure_category, result.failure_reason, result.failed_node, result.failed_tool,
        result.overall_judge_score, json.dumps(result.plan_quality_scores), json.dumps(result.raw_trace), result.timestamp
    ))
    conn.commit()
    conn.close()
