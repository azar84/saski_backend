#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os 

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, OpenAIMultiFunctionsAgent , ZeroShotAgent, ConversationalAgent
from langchain_core.prompts import ChatPromptTemplate , PromptTemplate
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import format_tool_to_openai_tool
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages, )
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool, StructuredTool, tool
from langchain import LLMChain , OpenAI
from tools.retreiver import retriever_tool
from langchain.chains import LLMChain
import uuid
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.render import format_tool_to_openai_function
from langchain.tools import Tool

from datetime import datetime


# In[2]:



# In[3]:



# In[4]:


#import default tools 

# Import Custom Tools 
from tools.retreiver import retriever_tool
from tools.ms365 import get_staff_availability , book_meeting
from tools.hubspot_tool import crm_update
from tools.airtable import get_feedback, get_id_by_thread_id  ,update_chat_record
from tools.general_tools import get_local_datetime

# ## Try the Langraph approach 

# In[5]:


from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    thread_id : str
    


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
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result }


# Haiku is faster and cheaper, but less accurate
# llm = ChatAnthropic(model="claude-3-haiku-20240307")
#llm = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
# You could swap LLMs, though you will likely want to update the prompts when
# doing so!
# from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4-turbo-preview")

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Hiqsense Smart Systems LTD or HiQSense for short. Your name is Saski. "
            "Hiqsense is a company specializing in designing and deploying LLM applications like chat bots , AI assistants and related applications "
            "Your knowledge is limited to the knowledgebase provided to you and the tools you have, don't create answers outside this context" 
            "Start any conversation by introducing yourself and ask the user how they needs your help"
            "After the first query by the user, ask them to provide you with their names and contact details so you can contact them if communication is interrupted then run the crm_update tool to save information."
            "Don't let the user leave the conversation without collecting their information and running the crm_update tool. "
            "At the end of each conversation, before you say goodbye, prompt the user to give feedback about your services from a scale from 1 to 5,Don't let the user go before asking for feedback on this scale, then use the get_feedback tool to record user feedback."
            "Don't create your own rating and conclusions about user feedback, if feedback not provided don't create it."
            " Use the provided tools to answer questions about the company, and company services, book a meeting, update CRM to generate leads, and provide information to assist the user's queries. "
            "When a user starts a conversation try to ask for their information to update our CRM, use the available tool and be smart to explain why you need this information."
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "You have tools to retrieve information about the company, book meetings with our staff, check availability of staff for meetings, update crm, get customer feedback."
            "Your responses shall be summarized not exceeding 500 characters"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

tools = [
    get_staff_availability ,
    book_meeting ,
    retriever_tool ,
    crm_update ,
    get_feedback ,
    get_local_datetime
    
    
    
    
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
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


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


from IPython.display import Image, display

try:
    display(Image(workflow.get_graph(xray=True).draw_mermaid_png()))
except:
    # This requires some extra dependencies and is optional
    pass


# In[10]:


thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        # The passenger_id is used in our flight tools to
        # fetch the user's flight information
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
}


# In[11]:


#get_input = input("What is Your Question")

#while True:
#    res = part_1_graph.invoke(
#        {"messages": ("user", get_input)}, config, stream_mode="values"
 #   )
 #   get_input = input(res['messages'][-1].content)


# In[12]:


def stream_flow(query : str  , thread_id : str):
    #chat_history = f'chat_hi
    config = {
    "configurable": {
         # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
                            } }
    result = workflow.stream({"messages": ("user", query+thread_id)}, config, stream_mode="values")
    for responses in result:
        response = responses
    # Add messages to chat history 
    ai_response = response['messages'][-1].content 

    update_chat_record(query , "User" , thread_id )
    update_chat_record(ai_response , "AI" , thread_id )
    

    
    return response['messages'][-1].content 
    









