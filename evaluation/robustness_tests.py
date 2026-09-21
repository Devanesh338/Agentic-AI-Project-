from .test_cases import TEST_CASES

# For now, robustness tests are defined directly in the main TEST_CASES list
# under categories like "missing_information", "conflicting_constraints",
# "invalid_input", and "extreme_budget".
# This file is reserved for future complex procedural robustness testing.

ROBUSTNESS_CASES = [tc for tc in TEST_CASES if tc.category in [
    "missing_information", 
    "conflicting_constraints", 
    "invalid_input", 
    "extreme_budget"
]]
