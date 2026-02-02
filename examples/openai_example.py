"""OpenAI auto-instrumentation example.

Requires: pip install agentpulse openai
Set OPENAI_API_KEY in your environment before running.
"""

from openai import OpenAI

from agentpulse import AgentPulse, trace, tool

# Initialize AgentPulse and patch OpenAI
ap = AgentPulse(endpoint="http://localhost:3000", api_key="ap_dev_default")
client = OpenAI()
ap.patch_openai(client)


@tool
def get_weather(city: str) -> str:
    """Simulate a weather lookup tool."""
    return f"72°F and sunny in {city}"


@trace(name="weather-agent")
def run_agent(question: str) -> str:
    # This LLM call is automatically traced with token/cost tracking
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful weather assistant."},
            {"role": "user", "content": question},
        ],
    )
    city = response.choices[0].message.content.strip()

    weather = get_weather(city)

    follow_up = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize the weather for the user."},
            {"role": "user", "content": f"Weather data: {weather}"},
        ],
    )
    return follow_up.choices[0].message.content


if __name__ == "__main__":
    result = run_agent("What's the weather in San Francisco?")
    print(f"Agent: {result}")

    ap.shutdown()
    print("Traces sent to AgentPulse collector.")
