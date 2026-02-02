"""Basic AgentPulse example — tracing without any LLM calls."""

from agentpulse import AgentPulse, trace, tool


# Initialize the client (self-hosted collector on localhost)
ap = AgentPulse(endpoint="http://localhost:3000", api_key="ap_dev_default")


@tool
def search_web(query: str) -> str:
    """Simulate a web search tool."""
    return f"Top results for: {query}"


@tool
def summarize(text: str) -> str:
    """Simulate a summarization tool."""
    return text[:100] + "..."


@trace(name="research-agent")
def run_agent(topic: str) -> str:
    results = search_web(topic)
    summary = summarize(results)
    return summary


if __name__ == "__main__":
    output = run_agent("latest developments in AI agents")
    print(f"Agent output: {output}")

    # Flush pending data before exiting
    ap.shutdown()
    print("Trace sent to AgentPulse collector.")
