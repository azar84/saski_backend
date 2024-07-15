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
Utilize this tool to consistently track the current date and time, enabling you to accurately interpret references to time-sensitive terms such as 'tomorrow,' 'next weekend,' 'yesterday,' and 'this weekend.' Ensure this tool is always used to maintain context awareness and provide precise responses.
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
from langchain_community.tools.tavily_search import TavilySearchResults


@tool
def llm_in_industry(industry: str):
  """
  If you are asked about the services we provide or the types of applications we can develop, follow these steps:

      1. First, inquire about the type of business or industry the user is interested in.
      2. Use this tool to search the web and find relevant applications and services that we can offer to clients in that specific industry utilizing LLM.
      3. Ensure your response to the user is formatted as an ordered list and does not mention the word 'Langchain'.
      4. Ensure that your answer is relevant to the business, omit any results that seems non related

      Args:
      - industry (str): The industry the user is interested in utilizing LLM applications.
  """
  results = []
  results.append(
      "AI Chat Bot, which can be used to enhance customer interaction, automate appointment bookings, and handle customer inquiries efficiently"
  )
  search_engine = TavilySearchResults()
  try:
    query_results = search_engine.invoke(
        f'How AI Assistants and AI Chatbots can help business in {industry} industry to save money and automate the operations'
    )
    res = [f"- {item['content']}" for item in query_results]
    results.extend(res)
    return results

  except:
    pass
