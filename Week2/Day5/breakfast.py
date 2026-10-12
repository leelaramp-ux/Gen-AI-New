import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 1. Load the secret API key from the .env file
load_dotenv()

# Verify the environment variable is loaded
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment or .env file.")

# 2. Initialize the ChatOpenAI model
# Note: temperature=0 makes output as deterministic and consistent as possible
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# 3. Create a strict, pinned prompt
prompt = (
    "Provide exactly 5 healthy breakfast ideas.\n"
    "Format requirements:\n"
    "- Numbered list (1 to 5)\n"
    "- Exactly one line per idea\n"
    "- Do not include any introductory or concluding text (no preamble, no commentary)."
)

# 4. Invoke the model
response = llm.invoke(prompt)

# --- LESSON: Try printing the raw response object first ---
# print("RAW MESSAGE OBJECT:")
# print(response)
# print("-" * 40)

# 5. Extract and print ONLY the content string
print(response.content)