from typing import List, Optional
from langchain.agents.agent import AgentExecutor
from langchain.agents.agent_toolkits.conversational_retrieval.openai_functions import _get_default_system_message
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.memory.token_buffer import ConversationTokenBufferMemory
from langchain.prompts import SystemMessagePromptTemplate
from langchain.prompts.chat import MessagesPlaceholder
from langchain.schema.memory import BaseMemory
from langchain.tools import Tool
from langchain_community.chat_models import ChatOpenAI

import os
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import tool
from langchain.llms import OpenAI
from langchain.agents import AgentType
from langchain.memory import ConversationBufferMemory
import warnings

warnings.filterwarnings("ignore")
from dotenv import load_dotenv

load_dotenv()

# In[23]:

vectorstore = Chroma(embedding_function=OpenAIEmbeddings(),
                     persist_directory='data/',
                     collection_name='hiqsense')
retriever = vectorstore.as_retriever()

# In[24]:

retreiver_tool_instructions = """search for information related to Hiqsene Smart Systems LTD, you will answer questions about 
their contact details, services, pricing, provide more details about their services and any other information included in the knowledge base, answer 
shall be summarized as much as possible, address the point without extra details, don't create your answers,
if you don't know just return: I have no information
"""
retriever_tool = create_retriever_tool(retriever, "knowledge_base_search",
                                       retreiver_tool_instructions)
