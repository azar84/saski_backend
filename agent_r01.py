#!/usr/bin/env python
# coding: utf-8

# In[1]:

import os

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, OpenAIMultiFunctionsAgent, ZeroShotAgent, ConversationalAgent
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import format_tool_to_openai_tool
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages, )
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool, StructuredTool, tool
from langchain import LLMChain, OpenAI
from tools.retreiver import retriever_tool
from langchain.chains import LLMChain
import uuid
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.render import format_tool_to_openai_function
from langchain.tools import Tool

from datetime import datetime

# In[2]:
# Open Assistant instructions in read mode
with open('instructions.txt', 'r') as file:
  # Read the contents of the file
  instructions = file.read()
# In[3]:

# In[4]:

#import default tools

# Import Custom Tools
from tools.retreiver import retriever_tool
from tools.ms365 import get_staff_availability, book_meeting
from tools.hubspot_tool import crm_update
from tools.airtable import get_feedback, get_id_by_thread_id, update_chat_record
from tools.general_tools import get_local_datetime, llm_in_industry

# ## Try the Langraph approach

# In[5]:

from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages


class State(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]
  thread_id: str


# In[6]:

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig


class Assistant:

  def __init__(self, runnable: Runnable):
    self.runnable = runnable

  def __call__(self, state: State, config: RunnableConfig):
    while True:

      state = {**state}
      result = self.runnable.invoke(state)
      # If the LLM happens to return an empty response, we will re-prompt it
      # for an actual response.
      if not result.tool_calls and (not result.content or isinstance(
          result.content, list) and not result.content[0].get("text")):
        messages = state["messages"] + [("user", "Respond with a real output.")
                                        ]
        state = {**state, "messages": messages}
      else:
        break
    return {"messages": result}


# Haiku is faster and cheaper, but less accurate
# llm = ChatAnthropic(model="claude-3-haiku-20240307")
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

# You could swap LLMs, though you will likely want to update the prompts when
# doing so!
# from langchain_openai import ChatOpenAI

#llm = ChatOpenAI(model="gpt-4-turbo-preview")

primary_assistant_prompt = ChatPromptTemplate.from_messages([
    ("system", instructions),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now())

tools = [
    get_staff_availability, book_meeting, retriever_tool, crm_update,
    get_feedback, get_local_datetime, llm_in_industry
]
assistant_runnable = primary_assistant_prompt | llm.bind_tools(tools)

# In[7]:

from langchain_core.runnables import RunnableLambda
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import ToolNode


def handle_tool_error(state) -> dict:
  error = state.get("error")
  tool_calls = state["messages"][-1].tool_calls
  return {
      "messages": [
          ToolMessage(
              content=f"Error: {repr(error)}\n please fix your mistakes.",
              tool_call_id=tc["id"],
          ) for tc in tool_calls
      ]
  }


def create_tool_node_with_fallback(tools: list) -> dict:
  return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)],
                                        exception_key="error")


def _print_event(event: dict, _printed: set, max_length=1500):
  current_state = event.get("dialog_state")
  if current_state:
    print(f"Currently in: ", current_state[-1])
  message = event.get("messages")
  if message:
    if isinstance(message, list):
      message = message[-1]
    if message.id not in _printed:
      msg_repr = message.pretty_repr(html=True)
      if len(msg_repr) > max_length:
        msg_repr = msg_repr[:max_length] + " ... (truncated)"
      print(msg_repr)
      _printed.add(message.id)


# In[8]:

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(tools))
# Define edges: these determine how the control flow moves
builder.set_entry_point("assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = SqliteSaver.from_conn_string(":memory:")
workflow = builder.compile(checkpointer=memory)

# In[9]:

# In[10]:


def stream_flow(query: str, thread_id: str):
  #chat_history = f'chat_hi
  config = {
      "configurable": {
          # Checkpoints are accessed by thread_id
          "thread_id": thread_id,
      }
  }
  result = workflow.stream(
      {
          "messages":
          ("user", "user message: " + query + ", thread_id: " + thread_id)
      },
      config,
      stream_mode="values")
  for responses in result:
    response = responses
  # Add messages to chat history
  ai_response = response['messages'][-1].content

  update_chat_record(query, "User", thread_id)
  update_chat_record(ai_response, "AI", thread_id)

  return response['messages'][-1].content
