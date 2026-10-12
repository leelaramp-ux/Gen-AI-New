import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# Updated import (silences LangGraphDeprecatedSinceV10)
from langchain.agents import create_agent

load_dotenv()

# --- Tool 1 ---
@tool
def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.
    Gender must be 'male' or 'female'. Returns calories per day needed at rest.
    """
    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return round(bmr, 2)

# --- Tool 2 ---
@tool
def calculate_water_intake(weight_kg: float, training_minutes: int) -> float:
    """Calculate daily recommended water intake in liters based on body weight and training minutes."""
    baseline_liters = weight_kg * 0.033
    additional_liters = (training_minutes / 30) * 0.35
    total = baseline_liters + additional_liters
    return round(total, 2)

tools = [calculate_bmr, calculate_water_intake]
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Instantiate without warnings
agent = create_agent(model, tools)

user_query = (
    "I am a 30-year-old female, weight 65 kg, height 168 cm. "
    "I plan to train for 60 minutes today. "
    "What is my BMR, and how much water should I drink today?"
)

result = agent.invoke({"messages": [("user", user_query)]})
print(result["messages"][-1].content)

# 4. Create the ReAct agent
# agent = create_react_agent(model, tools)

# 5. Ask a question requiring both tools
user_query = (
    "I am a 30-year-old female, weight 65 kg, height 168 cm. "
    "I plan to train for 60 minutes today. "
    "What is my BMR, and how much water should I drink today?"
)

print("Invoking agent...\n")
result = agent.invoke({"messages": [("user", user_query)]})

print("=" * 50)
print("AGENT EXECUTION TRACE (Step by Step):")
print("=" * 50)

for step, msg in enumerate(result["messages"], start=1):
    msg_type = type(msg).__name__
    print(f"\n[Step {step}] Message Type: {msg_type}")
    
    # Check if the model decided to call tools
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tool_call in msg.tool_calls:
            print(f"  👉 Decision: Call Tool '{tool_call['name']}' with args: {tool_call['args']}")
            
    # Check if this is the output returned by our Python function
    elif msg_type == "ToolMessage":
        print(f"  📥 Tool Return Value: {msg.content}")
        
    # Check if this is the final natural language answer
    elif msg_type == "AIMessage" and msg.content:
        print(f"  💬 Final AI Answer:\n{msg.content}")