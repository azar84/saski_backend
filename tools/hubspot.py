#!/usr/bin/env python
# coding: utf-8

# In[3]:


from hubspot import HubSpot
from dotenv import load_dotenv
import os
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional , Union , Type

load_dotenv()



# In[4]:


api_client = HubSpot()
api_client.access_token = os.environ['HUBSPOT_API_KEY']


# In[5]:


from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException

def add_contact(fname , lname , email, phone , company = None , address = None): 
    try:
        # Create a new contact with specified properties
        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
            properties={
                "firstname": fname,
                "lastname": lname ,
                "email": email,
                "phone": phone ,
                "company": company,
                "address" : address
            }
        )
        # Call the API to create the contact
        api_response = api_client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=simple_public_object_input_for_create
        )
        return ("Contact created successfully: ", api_response)
    except ApiException as e:
        return ("Exception when creating contact: %s\n" % e)


# In[6]:


@tool
def crm_update(
    fname: str = None,
    lname: str = None,
    email: str = None,
    phone: str = None,
    company: Optional[str] = None,
    address : Optional[str] = None
 

) -> dict:
    """
    Use this tool to collect user information and update our CRM
     Args:
        email (str): The email of the user. Defaults to None.
        fname (str): The first name of the user. Defaults to None.
        lname (str): The last name of the user. Defaults to None.
        phone (str): The phone number of the user. Defaults to None.
        company (Optional[str]): The company the user represents 
        address (Optional[str]): The address of the customer
    Returns:
        dict: A dictionary for the confirmation of crm update , just tell the user that we have saved his/her information and we can contact him
        if needed if the communciation is interrupted 
    """
   
    if  not fname:
        raise ValueError("First name is required.")
    if  not lname:
        raise ValueError("Last name is required.")
    if not email:
        raise ValueError("Email is required.")

    if  not phone:
         raise ValueError("Phone is required.")
    
 
   
   

    response   =     add_contact(fname , lname , email, phone , company , address )

        

   
    

    return response


# In[17]:


email = None
phone = None


# In[18]:


if not (email or  phone):
    print("error")


# In[ ]:




