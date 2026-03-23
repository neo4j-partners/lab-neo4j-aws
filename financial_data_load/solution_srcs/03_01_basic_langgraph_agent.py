"""
Basic LangGraph Agent

This solution demonstrates a ReAct-style agent using LangGraph
and ChatBedrockConverse with simple tool use.

Run with: uv run python main.py solutions <N>
"""

from typing import Literal
from datetime import datetime
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from config import BedrockConfig


# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

config = BedrockConfig()
MODEL_ID = config.model_id
REGION = config.region

# Derive BASE_MODEL_ID for cross-region inference profiles
if MODEL_ID.startswith("us.anthropic."):
    BASE_MODEL_ID = MODEL_ID.replace("us.anthropic.", "anthropic.")
elif MODEL_ID.startswith("global.anthropic."):
    BASE_MODEL_ID = MODEL_ID.replace("global.anthropic.", "anthropic.")
else:
    BASE_MODEL_ID = None

print(f"Model:          {MODEL_ID}")
print(f"Base Model:     {BASE_MODEL_ID}")
print(f"Region:         {REGION}")


# ---------------------------------------------------------------------------
# 2. Define Tools
# ---------------------------------------------------------------------------

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


tools = [get_current_time, add_numbers]
print(f"Defined {len(tools)} tools: {[t.name for t in tools]}")


# ---------------------------------------------------------------------------
# 3. Initialize the LLM
# ---------------------------------------------------------------------------

llm_kwargs = {
    "model": MODEL_ID,
    "region_name": REGION,
    "temperature": 0,
}

if BASE_MODEL_ID:
    llm_kwargs["base_model_id"] = BASE_MODEL_ID

llm = ChatBedrockConverse(**llm_kwargs)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

print(f"LLM initialized with {MODEL_ID}!")


# ---------------------------------------------------------------------------
# 4. Build the LangGraph Agent
# ---------------------------------------------------------------------------

def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    """Determine whether to continue to tools or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    """Call the LLM."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# Build the graph
graph = StateGraph(MessagesState)

# Add nodes
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode(tools))

# Add edges
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")

# Compile
agent = graph.compile()

print("Agent graph compiled successfully!")


# ---------------------------------------------------------------------------
# 5. Run the Agent
# ---------------------------------------------------------------------------

def run_agent(question: str):
    """Run the agent with a question and display the response."""
    print(f"Question: {question}")
    print("-" * 50)

    result = agent.invoke({
        "messages": [
            SystemMessage(content="You are a helpful assistant. Use tools when needed."),
            HumanMessage(content=question),
        ]
    })

    final_message = result["messages"][-1]
    print(f"\nResponse:\n{final_message.content}")
    return result


# ---------------------------------------------------------------------------
# 6. Query with Sample Financial Data
# ---------------------------------------------------------------------------

def load_financial_data() -> str:
    """Load sample SEC financial filing data from Lab 3."""
    data_path = (
        Path(__file__).resolve().parent.parent.parent
        / "Lab_3_Intro_to_Bedrock_and_Agents"
        / "sample_financial_data.txt"
    )
    with open(data_path, "r") as f:
        return f.read().strip()


def ask_about_data(question: str, context: str):
    """Ask the agent a question with context."""
    prompt = f"""Based on this SEC 10-K filing information:

{context}

Question: {question}"""
    return run_agent(prompt)


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------

def main():
    """Run demo queries."""
    # Test: Get current time
    run_agent("What is the current time?")
    print()

    # Test: Math calculation
    run_agent("What is 42 + 17?")
    print()

    # Test: Multiple tools
    run_agent("What time is it and what is 100 + 200?")
    print()

    # Load sample financial data and ask contextual questions
    financial_text = load_financial_data()
    lines = financial_text.split("\n")
    words = financial_text.split()
    print(f"Characters: {len(financial_text)}")
    print(f"Lines: {len(lines)}")
    print(f"Words: {len(words)}")
    print(f"Preview: {financial_text[:100]}...")
    print()

    ask_about_data(
        "What companies are mentioned and what are their key products?",
        financial_text,
    )
    print()

    ask_about_data(
        "What risk factors are mentioned and which companies face them?",
        financial_text,
    )


if __name__ == "__main__":
    main()
