import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Load environment variables
load_dotenv()

# 2. Initialize the model
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# 3. Create a dynamic prompt template
prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert nutritionist. Provide exactly {count} healthy breakfast ideas "
        "tailored for someone with the following dietary need: {diet}.\n"
        "Format requirements:\n"
        "- Numbered list (1 to {count})\n"
        "- Exactly one line per idea\n"
        "- No introductory or concluding remarks."
    ),
    ("human", "Give me {count} breakfast ideas for: {diet}")
])

# 4. Chain them together using the pipe operator (|)
# Prompt -> Model -> String Parser
chain = prompt_template | llm | StrOutputParser()

# 5. Run the chain with dynamic inputs
user_diet = "high-protein vegetarian"
user_count = 3

result = chain.invoke({"diet": user_diet, "count": user_count})

print(f"--- Breakfast Ideas for: {user_diet} ---")
print(result)