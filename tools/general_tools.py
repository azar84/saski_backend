#!/usr/bin/env python
# coding: utf-8

# In[2]:


from langchain.tools import BaseTool, StructuredTool, tool
from datetime import datetime
import pytz


# In[4]:


# Utils tools 
# Define the function to handle datetime with timezone

@tool 
def get_local_datetime(timezone_str):
    """
    Use this tool to make yourself aware about current date and time, so when user ask about tomorrow , today , yesterday you will be aware
    what dates and day of the week.
    If you don't know the user time zone, ask them to give to you. 
    """
    # Use the current UTC time as the base
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=pytz.utc)  # Set the timezone to UTC

    try:
        # Convert to the desired timezone
        local_timezone = pytz.timezone(timezone_str)
        local_time = utc_now.astimezone(local_timezone)
        week_day = local_time.strftime('%A')
        return f'today is {week_day} and it is {local_time.isoformat()}'
    except Exception as e:
        # Return error message if timezone conversion fails
        return str(e)


# In[ ]:




