#!/usr/bin/env python
# coding: utf-8

# In[6]:


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from agent_r01 import stream_flow


# In[7]:


app = FastAPI()


# In[8]:


session_id = str(uuid.uuid1()) 


# In[13]:


@app.post("/invoke/")
def process_query(data):
 
    try:
        response = stream_flow(data.query ,  data.thread_id)
        return {
            "output": response,
            
            "session_id":  data.thread_id
        }
    except:
        raise HTTPException(status_code=401, detail="Authentication Error")







# In[ ]:


@app.post("/session_id/")
def create_session_id(data: QueryData):
  #You need to setup a passcode to obtain a session id , here we used hiqsense
  if data.query == "hiqsense":
    session_id = str(uuid.uuid1())  # Generate a new session ID
    sessions.append(session_id)
    agents[f'agent_{session_id}'] = Memory_Agent(session_id).create_agent()
    return {"session_id": session_id}
  else:
    raise HTTPException(status_code=401, detail="Authentication Error")


# In[ ]:


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)

