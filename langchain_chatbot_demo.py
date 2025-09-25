import os
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from openai import OpenAI

from langgraph.checkpoint.memory import MemorySaver

# 1) LLM (use a valid model name)
llm = ChatOpenAI(model="gpt-5", temperature=0)

# 2) Image generation tool
client = OpenAI()  # Uses OPENAI_API_KEY

@tool
def generate_image(prompt: str, size: str = "1024x1024") -> Dict[str, str]:
    """Generates an image based on the given prompt and returns the URL."""
    img = client.images.generate(model="dall-e-3", prompt=prompt, size=size)
    return {"image_url": img.data[0].url}

# 3) Prompt: system rules + conversation history placeholder (messages) must be included!
SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an assistant that responds in English. Depending on the user's intent, use the 'generate_image' tool to create an image only when necessary. "
     "If it is not needed, respond concisely with text only. If you generate an image, provide the image URL at the end."),
    MessagesPlaceholder("messages"),  # ✅ Conversation history will be inserted here
])

# 4) Prepare checkpointer (in-memory)
checkpointer = MemorySaver()

# 5) Create the agent (with memory enabled)
agent = create_react_agent(
    model=llm,
    tools=[generate_image],
    prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,  # ✅ Added: saves/restores conversation
)

def ask(text: str, session_id: str = "default"):
    """
    If called with the same session_id, the conversation continues with previous context.
    Use different session_ids for different users/channels/tabs to keep contexts separate.
    """
    # LangGraph uses thread_id to distinguish sessions.
    config = {"configurable": {"thread_id": session_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config=config)
    msg = result["messages"][-1]
    return getattr(msg, "content", msg)

print(ask("Why does few-shot CoT works slightly better than zero-shot CoT? explain the reason.", session_id="demo"))
# 👉 Asking again in the same session: remembers previous answer and responds naturally
print(ask("How about training LLM into a model that answer in CoT way automatically when they solve inference problem? So that Users do not have to use CoT prompt every time when they solve inference problem.", session_id="demo"))
print(ask("Summarize answer to second question and make it into clear image", session_id="demo"))