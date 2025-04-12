# Let's check Google's ADK but without using Vertex AI and with a LiteLLM model
# Based on https://google.github.io/adk-docs/get-started/tutorial/

import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts

from dotenv import load_dotenv
load_dotenv()

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

# Configure ADK to use API keys directly (not Vertex AI for this multi-model setup)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Define constants for identifying the interaction context
APP_NAME_CLAUDE = "weather_tutorial_app_claude" # Unique app name
USER_ID_CLAUDE = "user_1_claude"
SESSION_ID_CLAUDE = "session_001_claude" # Using a fixed ID for simplicity

MODEL_CLAUDE_SONNET = "claude-3-5-sonnet-20240620"

# InMemorySessionService is simple, non-persistent storage for this tutorial.
session_service_claude = InMemorySessionService() # Create a dedicated service

# Create the specific session where the conversation will happen
session_claude = session_service_claude.create_session(
    app_name=APP_NAME_CLAUDE,
    user_id=USER_ID_CLAUDE,
    session_id=SESSION_ID_CLAUDE
)
print(f"Session created: App='{APP_NAME_CLAUDE}', User='{USER_ID_CLAUDE}', Session='{SESSION_ID_CLAUDE}'")

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: get_weather called for city: {city} ---")
    city_normalized = city.lower().replace(" ", "") # Basic input normalization

    # Mock weather data for simplicity
    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    # Best Practice: Handle potential errors gracefully within the tool
    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}

# Example tool usage (optional self-test)
# print(get_weather("New York"))
# print(get_weather("Paris"))

async def call_agent_async(query: str, runner: Runner, user_id: str, session_id: str):
  """Sends a query to the agent and prints the final response."""
  print(f"\n>>> User Query: {query}")

  # Prepare the user's message in ADK format
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "Agent did not produce a final response." # Default

  # Key Concept: run_async executes the agent logic and yields Events.
  # We iterate through events to find the final answer.
  async for event in runner.run_async(user_id=USER_ID_CLAUDE, session_id=SESSION_ID_CLAUDE, new_message=content):
      # You can uncomment the line below to see *all* events during execution
      # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

      # Key Concept: is_final_response() marks the concluding message for the turn.
      if event.is_final_response():
          if event.content and event.content.parts:
             # Assuming text response in the first part
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          # Add more checks here if needed (e.g., specific error codes)
          break # Stop processing events once the final response is found

  print(f"<<< Agent Response: {final_response_text}")


weather_agent_claude = None # Initialize to None
runner_claude = None      # Initialize runner to None

weather_agent_claude = Agent(
    name="weather_agent_claude",
    # Key change: Wrap the LiteLLM model identifier
    model=LiteLlm(model=MODEL_CLAUDE_SONNET),
    description="Provides weather information (using Claude Sonnet).",
    instruction="You are a helpful weather assistant powered by Claude Sonnet. "
                "Use the 'get_weather' tool for city weather requests. "
                "Analyze the tool's dictionary output ('status', 'report'/'error_message'). "
                "Clearly present successful reports or polite error messages.",
    tools=[get_weather], # Re-use the same tool
)
print(f"Agent '{weather_agent_claude.name}' created using model '{MODEL_CLAUDE_SONNET}'.")

# Create a runner specific to this agent and its session service
runner_claude = Runner(
    agent=weather_agent_claude,
    app_name=APP_NAME_CLAUDE,       # Use the specific app name
    session_service=session_service_claude # Use the specific session service
    )
print(f"Runner created for agent '{runner_claude.agent.name}'.")

if __name__ == "__main__":
    asyncio.run(call_agent_async(query = "Weather in London please.",
                        runner=runner_claude,
                        user_id=USER_ID_CLAUDE,
                        session_id=SESSION_ID_CLAUDE))
