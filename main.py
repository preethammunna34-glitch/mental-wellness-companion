import os
import operator
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.safety import evaluate_safety
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

# Initialize OpenRouter using the OpenAI wrapper
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="inclusionai/ling-3.2-flash:free",
    temperature=0.7
)

class AgentState(TypedDict):
    # Annotated with operator.add tells LangGraph to APPEND to memory, not overwrite!
    messages: Annotated[List[str], operator.add]
    risk_score: float
    route: str

def safety_node(state: AgentState):
    user_message = state["messages"][-1]
    safety_result = evaluate_safety(user_message)
    return {
        "risk_score": safety_result["risk_score"], 
        "route": safety_result["route"]
    }

def wellness_node(state: AgentState):
    """The main conversational agent powered by OpenRouter."""
    persona = '''
    You are a compassionate, empathetic mental wellness companion. 
    Your goal is to provide a safe space for the user to reflect. 
    
    CRITICAL RULES:
    1. Validate the user's feelings warmly and non-judgmentally.
    2. NEVER offer clinical diagnoses, medical advice, or medication suggestions.
    3. If the user feels overwhelmed, suggest a simple mindfulness or grounding exercise.
    4. Keep your responses conversational, concise, and easy to read (1-2 short paragraphs max).
    5. End your response with a gentle question to encourage reflection.
    6. You have a persistent memory of all past conversations. NEVER claim that you "don't carry memories" or "start fresh". Act like a continuous, familiar companion who remembers everything naturally.
    '''
    
    # Build the full conversation history for the LLM to read
    messages_to_llm = [SystemMessage(content=persona)]
    
    for msg in state["messages"]:
        if msg.startswith("Wellness Agent:") or msg.startswith("Crisis System:"):
            # Strip prefixes so the AI just sees normal conversation
            clean_msg = msg.replace("Wellness Agent: ", "").replace("Crisis System: ", "")
            messages_to_llm.append(AIMessage(content=clean_msg))
        else:
            messages_to_llm.append(HumanMessage(content=msg))
    
    # Generate the response using the FULL historical context
    response = llm.invoke(messages_to_llm)
    
    # Return only the new message, which operator.add will append to the state
    return {"messages": [f"Wellness Agent: {response.content}"]}

def crisis_node(state: AgentState):
    response = "I'm noticing you might be in distress. Please call 988 or reach out to emergency services immediately. Your safety is important."
    return {"messages": [f"Crisis System: {response}"]}

# Build and Compile the Graph
workflow = StateGraph(AgentState)
workflow.add_node("safety_monitor", safety_node)
workflow.add_node("wellness_agent", wellness_node)
workflow.add_node("crisis_protocol", crisis_node)

workflow.set_entry_point("safety_monitor")
workflow.add_conditional_edges(
    "safety_monitor",
    lambda x: x["route"],
    {
        "crisis_protocol": "crisis_protocol",
        "wellness_agent": "wellness_agent"
    }
)
workflow.add_edge("wellness_agent", END)
workflow.add_edge("crisis_protocol", END)

# Initialize memory and compile
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    print("--- Testing Live LLM Integration with OpenRouter ---")
    
    user_input = "I've been feeling really burnt out from my final year B.Tech project."
    print(f"User: {user_input}\n")
    
    config = {"configurable": {"thread_id": "demo_user_1"}}
    state = app.invoke({"messages": [user_input]}, config=config)
    
    print(state["messages"][-1])