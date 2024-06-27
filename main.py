#!/usr/bin/env python
# coding: utf-8

# In[6]:

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from agent_r01 import stream_flow
import timezonefinder, geopy, pandas, pyairtable
from fastapi.middleware.cors import CORSMiddleware

# In[7]:

app = FastAPI()
origins = [
    "http://localhost", "http://localhost:3000", "http://127.0.0.1:3000",
    "https://b44cdafb-a367-4ca1-8058-3b301d03471b-00-2xqkr7h33cvlj.janeway.replit.dev",
    "https://hiqsense.ca", "https://saski-ui.replit.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Data(BaseModel):
  query: str
  thread_id: str


# In[13]:


@app.post("/invoke/")
def process_query(data: Data):

  try:
    response = stream_flow(data.query, data.thread_id)
    return {"output": response, "session_id": data.thread_id}
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))


# In[ ]:

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
