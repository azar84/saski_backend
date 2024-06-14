#!/usr/bin/env python
# coding: utf-8

# ### Get Website Data and Store it in Chroma DB

# In[3]:

from langchain_community.document_loaders import SeleniumURLLoader
#from secrets import OpenAIKey
import requests
import os
from dotenv import load_dotenv
load_dotenv()

# In[4]:

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

# In[5]:

import chromadb
import warnings

warnings.filterwarnings('ignore')
# In[6]:
persist_dir = "../data/"
uploaded_documents_dir = "../uploads/"

# ### Get PDF data and store it in Chrma DB

# In[ ]:

loader = PyPDFLoader(f"{uploaded_documents_dir}Knowledge_Base.pdf")
pdf_data = loader.load()

# In[ ]:

# split it into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size= 750,
                                               chunk_overlap=250,
                                               add_start_index=True)
all_splits = text_splitter.split_documents(pdf_data)

# In[ ]:

# load it into Chroma
db = Chroma.from_documents(all_splits,
                           embedding=OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"]),
                           persist_directory=persist_dir,
                           collection_name='hiqsense')
db.persist()
