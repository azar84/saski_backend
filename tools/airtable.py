#!/usr/bin/env python
# coding: utf-8

# In[3]:


from dotenv import load_dotenv
import os
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional , Union , Type
from pyairtable import Api

load_dotenv()



# In[ ]:


api = Api(os.environ['AIRTABLE_API_KEY'])


# In[ ]:


#os.environ['AIRTABLE_API_KEY'] = 'patez2uPElvgUm5PO.7c4addcde22a70913129c9030da17e1941fd102f12391c87a61924e12b8f592e'
threads_table = api.table('appxKHhluzioMnerS', 'chat_threads')
messages_table = api.table('appxKHhluzioMnerS', 'messages')
feedback_table = api.table('appxKHhluzioMnerS', 'feedback')


# In[ ]:


def get_id_by_thread_id(thread_id, records):
    # Iterate over each record
    for record in records:
        # Check if 'fields' exists and contains 'thread_id'
        if 'fields' in record and 'thread_id' in record['fields']:
            # Check if 'thread_id' matches the provided thread_id
            if record['fields']['thread_id'] == thread_id:
                return record['id']  # Return the 'id' of the matching record
    return False  # Return None if no match is found

# This tool updates the record in Air Table , will be used manually in chat_stream 
def update_chat_record(message , type , thread_id):
    threads = threads_table.all()
    id = get_id_by_thread_id(thread_id, threads)
    if id:
                
                messages_table.create({'Type':type , 'message':message ,  'chat_threads': [id]})
    else:
                thread = threads_table.create({'thread_id': thread_id })
                id = thread['id']
                messages_table.create({'Type':type , 'message':message ,  'chat_threads': [id]})


# In[ ]:


def record_feedback(stars, thread_id , notes):
    feedback_table.create({ 'stars':stars ,  'chat_threads': [thread_id] , 'notes': notes})


@tool
def get_feedback(
    stars: int = None,
    thread_id: str = None,
    notes : Optional[str] = None
    ) -> dict:
    """
    Use this tool at the end of the conversation to request  user feedback about the service they receive,
    ask them to rate your assistance from 1 to 5, while 1 is not satisfied at all, 5 is very satisfied.
     Args:
        stars (int): The User rating of agent performance from 1 to 5
        thread_id (str): The thread id of the conversation,  you need to extract this from configurable data passed to the runnable
        notes (Optional[str] ) : Any comments or notes the user would like to provide about our services 
        
    Returns:
        dict: A dictionary for the confirmation of recording the userfeedback, just tell the user that we have received his/her feeabck and we 
        appreciate this as it will help us in improving our services. 
    """
   
    if  not stars:
        raise ValueError("Rating is required")
    if  not notes:
        return ("would you like to provide any notes for us to improve our services" )    
   
    threads = threads_table.all()
   
    thread_id = get_id_by_thread_id(thread_id , threads )
   
   

    response   =     record_feedback(stars, thread_id , notes)

        

   
    

    return response


# In[ ]:




