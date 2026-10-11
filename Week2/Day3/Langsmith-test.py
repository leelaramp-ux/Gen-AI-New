import os
os.environ  ["LANGCHAIN_TRACING_V2"] = "false"  

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

prompt = ChatPromptTemplate.from_template("Explain {topic} in one simple sentence.")
model = ChatOpenAI(model="gpt-4o-mini")
chain = prompt | model | StrOutputParser()

# This run is automatically recorded in LangSmith.
print(chain.invoke({"topic": "LangSmith"}))
