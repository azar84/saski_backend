#!/usr/bin/env python
# coding: utf-8

# In[1]:


from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional , Union , Type
from datetime import datetime , timedelta
import requests
import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pandas as pd

# add Azure Active Directory Application Secret here 


def get_access_token(client_id, client_secret, tenant_id):
    url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']


# In[15]:


import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

def get_timezone(city: str):

    # Initialize the geolocator
    geolocator = Nominatim(user_agent="timezone_finder")

    # Geocode the city to get latitude and longitude
    location = geolocator.geocode(city)
    if not location:
        raise ValueError(f"City '{city}' not found")

    # Initialize the timezone finder
    tf = TimezoneFinder()

    # Find the timezone based on latitude and longitude
    timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    if not timezone_str:
        raise ValueError(f"Timezone not found for city '{city}'")

    # Get the pytz timezone object
    timezone = pytz.timezone(timezone_str)
    return str(timezone)




@tool
def get_staff_availability( city):
    """
    Use this tool to find the availability of staff for a meeting then present it to user, first ask user about their city/location
    to find their time zone, After that run this tool to find  available slots in their time zone.
    Output shall be presented this way "Monday 31/05/2024: from 1:00 PM to 5:00PM (America/Regina) 
                                        Tuesday 04/06/2024: from 1:00 PM to 3:00PM and from 3:30PM to 5:00 PM (America/Regina), etc... 
    Don't assume the user's time zone, always ask for it or ask for the location and use the available function to determine the time zone                                    
    """
    access_token = get_access_token(client_id, client_secret, tenant_id)
    url = f'https://graph.microsoft.com/v1.0/solutions/bookingBusinesses/{user_id}/getStaffAvailability'

   
    # Define the time range to check for availability
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=14)  # Check for the next day
    # Example usage:
    timezone = get_timezone(city)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
    "staffIds": [
        "b940fb3b-06f3-44b4-b1b2-5998ec790c2a"
    ],
    "startDateTime": {
        "dateTime": start_time.isoformat(),
        "timeZone": "UTC"
    },
    "endDateTime": {
        "dateTime": end_time.isoformat(),
        "timeZone": "UTC"
    }
}
        
    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()
    response= response.json()['value'][0]['availabilityItems']
    time_table = pd.DataFrame(columns=[ 'Start', 'End'])
    for i in response:
    
            if i['status'] ==  "available":
                       
                time_table.loc[i['startDateTime']['dateTime'], "Date"] = pd.to_datetime(i['startDateTime']['dateTime'])
                time_table.loc[i['startDateTime']['dateTime'], "Start"] = i['startDateTime']['dateTime']
                time_table.loc[i['startDateTime']['dateTime'], "End"]= i['endDateTime']['dateTime']
                
    time_table = time_table.set_index("Date" , inplace= False)
    time_table['Start'] = pd.to_datetime(time_table['Start'])
    time_table['End'] = pd.to_datetime(time_table['End'])
    time_offset = datetime.now() + timedelta(hours = 12)
    time_table = time_table.loc[time_offset:]
    #convert time zone
    time_table = time_table.tz_localize('GMT+0').tz_convert(timezone)
    time_table['Start'] = time_table['Start'].dt.tz_localize('GMT+0').dt.tz_convert(timezone)
    time_table['End'] = time_table['End'].dt.tz_localize('GMT+0').dt.tz_convert(timezone)
    time_table['Week_Day'] = time_table['Start'].dt.day_name()

    
    
         
    return time_table


# In[5]:


def is_time_within_range(input_time, df):
    input_time = parser.parse(input_time)
    input_time = input_time.astimezone(pd.Timestamp.now().tz)  # Adjust timezone to local timezone of the DataFrame
    
    # Check if the time is within any intervals
    for index, row in df.iterrows():
        if row['Start'] <= input_time <= row['End']:
            return 

def book_appointment(name,email,phone,note , time, time_zone , address = None):
    from pytz import timezone
    # configuration
   
    online = True
    location = "MS Teams Meeting" 
    location_name = "Online Meeting" 
    service_id = "582faf32-5195-44fc-9c2c-3dae71dd8834"
    


    access_token = get_access_token(client_id, client_secret, tenant_id)
    url = f'https://graph.microsoft.com/v1.0/solutions/bookingBusinesses/{user_id}/appointments'
    ## pass the time and time zone 
    # Define the time range to check for availability
    start_time = pd.to_datetime(time)
    end_time = start_time + timedelta(minutes=30)  # Check for the next day
  

    
    tz = timezone(time_zone)

    start_time =  (tz.normalize(tz.localize(start_time)).astimezone(pytz.utc)).isoformat()
    end_time =  (tz.normalize(tz.localize(end_time)).astimezone(pytz.utc)).isoformat()
    #print(start_time,"  ", end_time )
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
    "@odata.type": "#microsoft.graph.bookingAppointment",
    "customerTimeZone":time_zone,
    "smsNotificationsEnabled": False,
    "endDateTime": {
        "@odata.type": "#microsoft.graph.dateTimeTimeZone",
        "dateTime": end_time,
        "timeZone": "UTC"
    },
    "isLocationOnline": online,
    "optOutOfCustomerEmail": False,
    "anonymousJoinWebUrl": None,
    "postBuffer": "PT15M",
    "preBuffer": "PT0M",
    "price": 0.0,
    "priceType@odata.type": "#microsoft.graph.bookingPriceType",
    "priceType": "free",
    "customerNotes" : "Check this note "    ,     
    "reminders@odata.type": "#Collection(microsoft.graph.bookingReminder)",
   
    "serviceId": service_id,
    "serviceLocation": {
        "@odata.type": "#microsoft.graph.location",
        "address": {
            "@odata.type": "#microsoft.graph.physicalAddress",
            "city": location,
            "countryOrRegion": "",
            "postalCode": "",
            "postOfficeBox": None,
            "state": "",
            "street": "",
            "type@odata.type": "#microsoft.graph.physicalAddressType",
            "type": None
        },
        "coordinates": None,
        "displayName": location_name,
        "locationEmailAddress": None,
        "locationType@odata.type": "#microsoft.graph.locationType",
        "locationType": None,
        "locationUri": None,
        "uniqueId": None,
        "uniqueIdType@odata.type": "#microsoft.graph.locationUniqueIdType",
        "uniqueIdType": None
    },
    "serviceName": "Discovery Meeting",
    "serviceNotes": "Meet with Hiqsense to understand your business needs",
    "staffMemberIds": [staff_id],    
    
    
    "startDateTime": {
        "@odata.type": "#microsoft.graph.dateTimeTimeZone",
        "dateTime": start_time,
        "timeZone": "UTC"
    },
    "maximumAttendeesCount": 1,
    "filledAttendeesCount": 1,
    "customers@odata.type": "#Collection(microsoft.graph.bookingCustomerInformation)",
    "customers": [
        {
            "@odata.type": "#microsoft.graph.bookingCustomerInformation",
            "customerId": "",
            "name": name,
            "emailAddress": email,
            "phone": phone,
            "notes": "This is the customer Note" ,
            "location": {
                "@odata.type": "#microsoft.graph.location",
                "displayName": "Customer",
                "locationEmailAddress": None,
                "locationUri": "",
                "locationType": None,
                "uniqueId": None,
                "uniqueIdType": None,
                "address": {
                    "@odata.type": "#microsoft.graph.physicalAddress",
                    "street": address,
                    "city": "",
                    "state": "",
                    "countryOrRegion": "",
                    "postalCode": ""
                },
                "coordinates": {
                    "altitude": None,
                    "latitude": None,
                    "longitude": None,
                    "accuracy": None,
                    "altitudeAccuracy": None
                }
            },
            "timeZone": time_zone ,

        }
    ]
}
        
    response = requests.post(url, headers=headers , json = params)
    response.raise_for_status()
    response= response.json()

    return response





# In[6]:


@tool
def book_meeting(
    email: str = None,
    name: str = None,
    phone: str = None,
    note: Optional[str] = None,
    start_date_time: str = None,
    time_zone : str = None ,
    address : Optional[str] = None
 

) -> dict:
    """
    Use this tool after checking staff availability,to book a meeting based on start time, get name, email, phone , start date and time of the meeting, the user timezone, address
    and any note the user would like to provide for the meeting.Don't book a meeting outside the staff availability.
     Args:
        email (str): The email of the user. Defaults to None.
        name (str): The name of the user. Defaults to None.
        phone (str): The phone number of the user. Defaults to None.
        start_date_time (str) : The date and time of the meeting in string format , you need to convert to a format 
        acceptable by python datetime function
        time_zone (str) : The user time zone, after receiving it convert it to a format acceptable by pytz
        note (Optional[str]): The note the user would like to leave for the company to prepare for the meeting. Defaults to None.
        address (Optional[str]): The address of the customer
      
    Returns:
        dict: A dictionary for the meeting booking with information about time, date , name and phone
    """
   
    if  not name:
        raise ValueError("Name is required.")

    if not email:
        raise ValueError("Email is required.")

    if  not phone:
         raise ValueError("Phone is required.")
    if  not time_zone:
         raise ValueError("Timezone is required.")
    if  not start_date_time:
         raise ValueError("Meeting start date and time are required.")
    elif (is_time_within_range(start_date_time,get_staff_availability(time_zone) )):
         raise ValueError("Please choose a time within the availabe slots.")
 
   
   

    response   =     book_appointment(name,email,phone,note , start_date_time, time_zone , address)

        

   
    

    return response


# In[16]:


avail = get_staff_availability("Irbid")


# In[17]:


avail


# In[9]:


start = "2024-06-17 14:00:00-06:00"


# In[10]:


if start in avail:
    print("time within the limits")

else:
    print("time outside the limit")


# In[11]:


from dateutil import parser
# Function to check if input time is within the range

def is_time_within_range(input_time, df):
    input_time = parser.parse(input_time)
    input_time = input_time.astimezone(pd.Timestamp.now().tz)  # Adjust timezone to local timezone of the DataFrame
    
    # Check if the time is within any intervals
    for index, row in df.iterrows():
        if row['Start'] <= input_time <= row['End']:
            return True
    return False


# In[12]:


is_time_within_range(start , avail)


# In[ ]:




