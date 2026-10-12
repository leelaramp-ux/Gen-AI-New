import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

# 1. Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

# 2. Prompt template with a placeholder for past conversation turns
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful, friendly personal nutritionist assistant."),
    MessagesPlaceholder(variable_name="history"),  # Past messages get injected here
    ("human", "{question}")                        # Current user question
])

# 3. Base chain
base_chain = prompt | llm | StrOutputParser()

# 4. Session memory store (keeps separate histories per session_id)
session_store = {}

def get_session_history(session_id: str):
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

# 5. Wrap the chain with message history
chat_chain = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 6. Test a multi-turn conversation under one session
config = {"configurable": {"session_id": "user_session_1"}}

print("--- Turn 1 ---")
r1 = chat_chain.invoke({"question": "Hi, my name is Leela and I am preparing for a 10k run."}, config=config)
print("Assistant:", r1)

print("\n--- Turn 2 (Referencing past context) ---")
r2 = chat_chain.invoke({"question": "What was my name, and what event am I training for?"}, config=config)
print("Assistant:", r2)

print("\n--- Turn 3 (Building on prior turns) ---")
r3 = chat_chain.invoke({"question": "Suggest a pre-run snack suitable for that event."}, config=config)
print("Assistant:", r3)
