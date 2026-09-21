import os

# Evaluation Thresholds
MAX_STEPS = 30
MAX_RUNTIME_SECONDS = 120
MAX_IDENTICAL_TOOL_CALLS = 3

# LLM Judge Settings
ENABLE_LLM_JUDGE = True
JUDGE_MODEL = "openai/gpt-oss-120b" # Using the existing ChatGroq model

# Cost Tracking (per 1M tokens in USD)
# Defaulting to approximate Llama 3 70B pricing, user can override
INPUT_COST_PER_1M_TOKENS = 0.59
OUTPUT_COST_PER_1M_TOKENS = 0.79

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "evaluation.db")
