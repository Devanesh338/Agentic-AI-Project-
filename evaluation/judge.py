import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from .config import JUDGE_MODEL

class LLMJudge:
    def __init__(self):
        self.llm = ChatGroq(model=JUDGE_MODEL)

    def evaluate_plan(self, query: str, itinerary: str) -> dict:
        prompt = f"""
You are an expert travel evaluation judge.
Evaluate the following travel itinerary based on the user's query.

User Query:
{query}

Itinerary:
{itinerary}

Score the following dimensions from 1 to 5 (where 1 is poor and 5 is excellent).
Respond ONLY with a valid JSON object in this exact format, with no markdown formatting or extra text:
{{
  "relevance": 4,
  "completeness": 5,
  "consistency": 4,
  "feasibility": 4,
  "clarity": 5,
  "reasoning": "Brief explanation of the scores."
}}
"""
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a strict and objective JSON evaluation system."),
                HumanMessage(content=prompt)
            ])
            # Parse JSON
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            return {
                "relevance": 0,
                "completeness": 0,
                "consistency": 0,
                "feasibility": 0,
                "clarity": 0,
                "reasoning": f"Judge evaluation failed: {e}"
            }
