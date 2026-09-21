# Agentic AI Evaluation Framework

This module provides an isolated, production-grade evaluation subsystem for the `Multi_Agent_System_With_Mcp2` project. It evaluates the agentic workflow across planning, tool usage, safety (consent), and booking capabilities.

## Execution

To run an evaluation batch:
```bash
python -m evaluation.runner
```

To view the dashboard:
```bash
streamlit run evaluation/dashboard.py
```

To export results to JSON or CSV:
```bash
python -m evaluation.report_generator <run_id> csv
```

## Metrics Dictionary

### Task Success Rate
- **Definition:** The percentage of tests that successfully completed end-to-end (planning + safety + booking).
- **Formula:** `successful tasks / total tasks × 100`

### Requirement Satisfaction Rate
- **Definition:** Measures if the explicitly stated requirements (origin, destination, budget, duration) were correctly extracted and respected by the agent.
- **Formula:** `satisfied requirements / total requirements × 100`

### Constraint Satisfaction Rate
- **Definition:** Similar to requirement satisfaction, ensures strict boundaries (like maximum budget) are met.
- **Formula:** `satisfied constraints / total constraints × 100`

### Tool Execution Success Rate
- **Definition:** The percentage of MCP tool calls that returned successfully without throwing errors.
- **Formula:** `successful tool calls / total tool calls × 100`

### Tool Selection Accuracy
- **Definition:** Measures if the agent selected the *correct* subset of tools required to solve the task.
- **Formula:** `correct required tools / required tools × 100`

### Unnecessary Tool Call Rate
- **Definition:** Penalizes the agent for repeatedly calling the exact same tool with the exact same arguments uselessly.
- **Formula:** `unnecessary tool calls / total tool calls × 100`

### Booking Success Rate
- **Definition:** The percentage of tasks where a final booking was successfully confirmed (when consent was given).
- **Formula:** `successful booking simulations / booking attempts × 100`
- **Note:** This reflects simulated booking success, as provider APIs are mocked.

### Consent Compliance Rate
- **Definition:** A safety metric ensuring that the `consent_gate` was correctly respected. If the user rejects consent, the booking MUST NOT be confirmed.
- **Formula:** `correctly consent-gated actions / consent-required actions × 100`

### Average Steps
- **Definition:** The average number of nodes + tool calls executed per task.
- **Formula:** `total execution steps / total tasks`

### Average Latency
- **Definition:** The average wall-clock time required to process a query end-to-end.
- **Formula:** `total execution time / total tasks`

### Ticket Accuracy
- **Definition:** Validates that the final booking details (ticket) contain the correct origin and destination data.
- **Formula:** `correct ticket fields / expected ticket fields × 100`

## Structure
- `runner.py`: Executes the evaluation.
- `evaluator.py`: Contains evaluation logic.
- `trace_logger.py`: Captures LangChain & MCP traces.
- `dashboard.py`: Streamlit visualization.
- `test_cases.py`: The dataset.
