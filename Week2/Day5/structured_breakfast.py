import os
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# 1. Define the schema for a single breakfast idea
class Recipe(BaseModel):
    name: str = Field(description="Name of the breakfast dish")
    estimated_calories: int = Field(description="Estimated calories per serving")
    protein_grams: int = Field(description="Estimated protein in grams")
    ingredients: List[str] = Field(description="Key ingredients needed")
    prep_time_minutes: int = Field(description="Preparation time in minutes")

# 2. Define the container schema for the full response
class BreakfastPlan(BaseModel):
    diet_type: str = Field(description="The dietary category requested")
    recipes: List[Recipe] = Field(description="List of breakfast recipes")

# 3. Initialize the model and bind the schema
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(BreakfastPlan)

# 4. Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional nutritionist. Provide structured meal plans based on requests."),
    ("human", "Give me {count} healthy breakfast options for a {diet} diet.")
])

# 5. Build the chain
chain = prompt | structured_llm

# 6. Invoke the chain
result: BreakfastPlan = chain.invoke({"count": 3, "diet": "high-protein vegan"})

# 7. Treat it as pure Python attributes (not strings!)
print(f"Plan for: {result.diet_type}\n" + "=" * 40)
for idx, r in enumerate(result.recipes, start=1):
    print(f"{idx}. {r.name}")
    print(f"   ⏱ Prep: {r.prep_time_minutes} mins | ⚡ Calories: {r.estimated_calories} kcal | 🍗 Protein: {r.protein_grams}g")
    print(f"   🛒 Ingredients: {', '.join(r.ingredients)}")
    print("-" * 40)