from .schemas import EvaluationResult, ExpectedResult
from typing import Dict, Any

def normalize_text(text: str) -> str:
    if not text:
        return ""
    return str(text).strip().lower()

def calculate_extraction_accuracy(actual: dict, expected: ExpectedResult) -> float:
    expected_fields = ["origin", "destination", "duration", "budget", "transport"]
    total = 0
    correct = 0
    
    for field in expected_fields:
        exp_val = getattr(expected, field, None)
        if exp_val is not None:
            total += 1
            act_val = actual.get(field)
            if normalize_text(act_val) == normalize_text(exp_val):
                correct += 1
                
    if total == 0:
        return 100.0
    return (correct / total) * 100.0

def calculate_tool_metrics(trace: Dict[str, Any], expected: ExpectedResult) -> dict:
    tools = trace.get("tools", [])
    total_tools = len(tools)
    if total_tools == 0:
        return {"accuracy": 0.0, "success": 0.0, "unnecessary": 0.0}
    
    successful_tools = sum(1 for t in tools if t.get("success", False))
    success_rate = (successful_tools / total_tools) * 100.0
    
    # Check if required tools were called
    expected_tools = expected.expected_tools
    required = len(expected_tools)
    if required > 0:
        called_names = [t.get("tool_name") for t in tools]
        correct_calls = sum(1 for et in expected_tools if et in called_names)
        accuracy = (correct_calls / required) * 100.0
    else:
        accuracy = 100.0
        
    # Heuristic for unnecessary: if same tool called > 3 times with same args
    tool_counts = {}
    for t in tools:
        sig = str(t.get("tool_name")) + str(t.get("arguments"))
        tool_counts[sig] = tool_counts.get(sig, 0) + 1
        
    unnecessary = sum(count - 1 for count in tool_counts.values() if count > 1)
    unnecessary_rate = (unnecessary / total_tools) * 100.0 if total_tools > 0 else 0.0
    
    return {
        "accuracy": accuracy,
        "success": success_rate,
        "unnecessary": unnecessary_rate
    }

def calculate_consent_compliance(trace: Dict[str, Any], expected: ExpectedResult, user_approved: bool) -> float:
    if not expected.consent_required:
        return 100.0
        
    # If consent required and user approved -> confirmation is expected
    # If consent required and user rejected -> confirmation MUST NOT happen
    confirm_called = any(t.get("tool_name") == "confirm_booking" for t in trace.get("tools", []))
    
    if user_approved:
        # If they approved, it doesn't strictly have to confirm if a previous step failed, but compliance isn't violated.
        # Actually, if they approve and it books, that's fine.
        return 100.0
    else:
        # If they rejected, and it called confirm_booking, that is a violation!
        if confirm_called:
            return 0.0
        return 100.0
        
def calculate_ticket_accuracy(actual_details: str, expected: ExpectedResult) -> float:
    # Basic check if it has origin and destination
    if not expected.origin and not expected.destination:
        return 100.0
        
    if not actual_details:
        return 0.0
        
    actual_norm = normalize_text(actual_details)
    correct = 0
    total = 0
    if expected.origin:
        total += 1
        if normalize_text(expected.origin) in actual_norm:
            correct += 1
    if expected.destination:
        total += 1
        if normalize_text(expected.destination) in actual_norm:
            correct += 1
            
    if total == 0:
        return 100.0
    return (correct / total) * 100.0
