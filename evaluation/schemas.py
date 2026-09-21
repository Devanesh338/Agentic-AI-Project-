from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ExpectedResult(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    duration: Optional[int] = None
    budget: Optional[float] = None
    transport: Optional[str] = None
    hotel_required: Optional[bool] = None
    consent_required: bool = True
    expected_tools: List[str] = Field(default_factory=list)
    expected_requirements: List[str] = Field(default_factory=list)

class EvaluationTestCase(BaseModel):
    id: str
    category: str
    query: str
    expected: ExpectedResult

class EvaluationResult(BaseModel):
    test_case_id: str
    query: str
    
    # Extraction
    structured_request: Dict[str, Any] = Field(default_factory=dict)
    expected_request: Dict[str, Any] = Field(default_factory=dict)
    
    # High-level success
    task_success: bool = False
    planning_success: bool = False
    booking_success: bool = False
    
    # Satisfaction
    requirement_satisfaction: float = 0.0
    constraint_satisfaction: float = 0.0
    
    # Tool metrics
    tool_selection_accuracy: float = 0.0
    tool_execution_success: float = 0.0
    unnecessary_tool_calls: float = 0.0
    
    # Safety
    consent_compliance: float = 0.0
    unauthorized_booking: float = 0.0
    unauthorized_payment: float = 0.0
    invalid_actions: float = 0.0
    
    # Ticket accuracy
    ticket_accuracy: float = 0.0
    
    # Steps
    average_steps: float = 0.0
    total_steps: int = 0
    
    # Latency (seconds)
    latency: float = 0.0
    planning_latency: float = 0.0
    booking_latency: float = 0.0
    mcp_latency: float = 0.0
    
    # Efficiency
    llm_calls: int = 0
    mcp_calls: int = 0
    token_usage: Optional[int] = None
    estimated_cost: Optional[float] = None
    cost_efficiency: Optional[float] = None
    
    # Robustness / Flow
    loop_detected: bool = False
    timeout: bool = False
    
    # Taxonomy
    failure_category: Optional[str] = None
    failure_reason: Optional[str] = None
    failed_node: Optional[str] = None
    failed_tool: Optional[str] = None
    
    # Qualitative
    plan_quality_scores: Dict[str, int] = Field(default_factory=dict)
    overall_judge_score: float = 0.0
    
    # Tracing
    raw_trace: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
