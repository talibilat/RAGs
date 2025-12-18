import yaml
import asyncio
import sys
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from app.agent.router import route_intent
from app.agent.state import AgentState

async def run_evals():
    with open("app/evals/cases.yaml", "r") as f:
        data = yaml.safe_load(f)
        
    cases = data["cases"]
    passed = 0
    total = len(cases)
    
    print(f"Running {total} eval cases...")
    
    for case in cases:
        user_input = case["input"]
        expected = case["expected_intent"]
        
        # Mock state
        state = {
            "messages": [("user", user_input)],
            "user_info": {"id": 1, "role": "pm", "email": "bob@example.com"}
        }
        
        result = await route_intent(state)
        predicted = result["intent"]
        
        if predicted == expected:
            print(f"[PASS] '{user_input}' -> {predicted}")
            passed += 1
        else:
            print(f"[FAIL] '{user_input}' -> {predicted} (expected {expected})")
            
    print(f"\nResults: {passed}/{total} passed.")
    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_evals())
