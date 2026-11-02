
import asyncio
import os

from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


# Step 1: Load environment variables from .env
load_dotenv()

# Step 2: Read the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY is missing. "
        "Please configure it in your .env file."
    )

# Step 3: Create the OpenAI model client
model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=api_key
)

# Step 4: Create the HR Assistant Agent
agent = AssistantAgent(
    name="employment_lawyer",
    model_client=model_client,
    system_message="You are an employment lawyer."
)


# Step 5: Create an asynchronous main function
async def main():

    try:
        # Ask the HR agent to generate a job description
        await Console(
            agent.run_stream(
                task=(
                    "Write a job description for a Junior Python Developer. "
                    "Provide exactly five bullet points, "
                    "with one sentence per bullet point. "
                    "Do not include a title or introduction."
                )
            )
        )

    finally:
        # Step 6: Close the model client
        await model_client.close()


# Step 7: Run the asynchronous program
if __name__ == "__main__":
    asyncio.run(main())
