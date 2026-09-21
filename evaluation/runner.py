import asyncio
import uuid
import datetime
from langchain_core.messages import HumanMessage
import json

from evaluation.test_cases import TEST_CASES
from evaluation.trace_logger import TraceLogger, patch_mcp_calls, unpatch_mcp_calls
from evaluation.storage import init_db, save_run, save_result
from evaluation.evaluator import Evaluator
from evaluation.config import ENABLE_LLM_JUDGE

# App imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "booking_system"))

from main import app as planning_app
from app.agents.booking_orchestrator import booking_app
from app.database.database import Base, engine

def setup_db():
    Base.metadata.create_all(bind=engine)
    init_db()

async def execute_case(test_case, evaluator):
    print(f"Running Test Case: {test_case.id} - {test_case.category}")
    
    logger = TraceLogger()
    originals = patch_mcp_calls(logger)
    
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "callbacks": [logger]
    }
    
    # 1. Planning Phase
    user_input = test_case.query
    plan_result = {}
    
    try:
        plan_result = await planning_app.ainvoke(
            {
                "messages": [HumanMessage(content=user_input)],
                "user_query": user_input,
                "origin": "",
                "destination": "",
                "departure_date": "",
                "return_date": "",
                "travelers": 1,
                "budget": 0.0,
                "transport_preference": "",
                "flight_results": "",
                "hotel_results": "",
                "weather_results": "",
                "itinerary": "",
                "llm_calls": 0,
            },
            config=config,
        )
    except Exception as e:
        print(f"Planning failed: {e}")

    # 2. Booking Phase
    booking_result = {}
    user_approved_consent = True
    
    # If safety case asks to reject consent, we simulate rejection.
    # Otherwise simulate approval.
    if test_case.category == "safety" and "reject" in test_case.query.lower():
        user_approved_consent = False

    try:
        booking_config = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "callbacks": [logger]
        }
        
        book_res = await booking_app.ainvoke(
            {
                "messages": [],
                "user_id": "eval_user",
                "itinerary": plan_result.get("itinerary", ""),
                "origin": plan_result.get("origin", ""),
                "destination": plan_result.get("destination", ""),
                "departure_date": plan_result.get("departure_date", ""),
                "return_date": plan_result.get("return_date", ""),
                "travelers": plan_result.get("travelers", 1),
                "budget": plan_result.get("budget", 0.0),
                "session_id": "",
                "consent_status": "PENDING",
                "booking_status": "",
                "booking_details": ""
            },
            config=booking_config
        )
        
        if user_approved_consent:
            # Simulate explicit backend consent
            session_id = book_res.get("session_id")
            if session_id:
                from app.database.database import SessionLocal
                from app.services.consent_service import request_consent, approve_consent
                from app.services.booking_service import get_booking_session
                from app.schemas.booking_schema import ConsentRequest
                db = SessionLocal()
                try:
                    session_record = get_booking_session(db, session_id)
                    actual_amount = session_record.total_amount if session_record else 1000.0
                    c_req = ConsentRequest(user_id="eval_user", amount=actual_amount, currency="INR")
                    c_rec = request_consent(db, session_id, c_req)
                    approve_consent(db, session_id, c_rec.id)
                except Exception as e:
                    print(f"Consent DB error: {e}")
                finally:
                    db.close()
            
            # Resume booking
            booking_result = await booking_app.ainvoke(None, config=booking_config)
        else:
            booking_result = book_res
            
    except Exception as e:
        print(f"Booking failed: {e}")
        
    unpatch_mcp_calls(originals)
    
    trace = logger.finish()
    
    eval_result = evaluator.evaluate(test_case, plan_result, booking_result, trace, user_approved_consent)
    return eval_result

async def run_evaluation():
    print("================================================")
    print("AGENTIC TRAVEL SYSTEM EVALUATION")
    print("================================================")
    
    setup_db()
    evaluator = Evaluator(use_llm_judge=ENABLE_LLM_JUDGE)
    
    results = []
    
    for case in TEST_CASES:
        res = await execute_case(case, evaluator)
        results.append(res)
        
    # Summarize
    total = len(results)
    e2e = sum(1 for r in results if r.task_success)
    plan = sum(1 for r in results if r.planning_success)
    book = sum(1 for r in results if r.booking_success)
    
    overall_success_rate = (e2e / total) * 100.0 if total > 0 else 0.0
    
    # Save to DB
    run_id = save_run(datetime.datetime.now().isoformat(), total, overall_success_rate)
    for r in results:
        save_result(run_id, r)
        
    print("\n================================================")
    print(f"Test Cases:                 {total}")
    print(f"End-to-End Success:         {overall_success_rate:.1f}%")
    print(f"Planning Success:           {(plan/total)*100:.1f}%")
    print(f"Booking Success:            {(book/total)*100:.1f}%")
    print("================================================")
    
    print("Evaluation completed. Results saved to evaluation.db")
    print("Use Streamlit Dashboard to view detailed metrics.")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
