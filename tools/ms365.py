#!/usr/bin/env python
# coding: utf-8

# In[1]:

from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional, Union, Type
from datetime import datetime, timedelta
import requests
import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pandas as pd

# add Azure Active Directory Application Secret here
# Configuration for MS Graph API :
client_id = 'd1b63a88-9266-4bbd-97a0-81c448bb3bfe'
client_secret = 'nOX8Q~LDaAe14A2pDuFs5_SRHk4j5R0wTm0s5bDc'
tenant_id = '240814aa-0b26-42e4-8a4c-408f1250c440'
user_id = 'hiqsense@hiqsense.ca'
staff_id = 'b940fb3b-06f3-44b4-b1b2-5998ec790c2a'


def get_access_token(client_id, client_secret, tenant_id):
  url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
  headers = {'Content-Type': 'application/x-www-form-urlencoded'}
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
def get_staff_availability(city=None, start_time=None):
  """
    Use this tool to find the availability of staff for a meeting then present it to the user, 
    first ask the user about their city/location to find their time zone. 
    After that run this tool to find available slots in their time zone.
    The nearest meeting shall be at least 12 hours from the current time.
    Output shall be presented this way "Monday 31-May-2024: from 1:00 PM to 5:00 PM (America/Regina)" 
                                       "Tuesday 04-Jun-2024: from 1:00 PM to 3:00 PM and from 3:30 PM to 5:00 PM (America/Regina)", etc...
    Don't assume the user's time zone, always ask for it or ask for the location and use the available function to determine the time zone.

    Args:
        city (str): The city or location of the user to calculate their time zone.
        start_time (str): The desired starting date for the meeting in this format '%Y-%m-%d %H:%M:%S'
    """
  access_token = get_access_token(client_id, client_secret, tenant_id)
  url = f'https://graph.microsoft.com/v1.0/solutions/bookingBusinesses/{user_id}/getStaffAvailability'

  # Define the time range to check for availability
  if start_time:
    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
  else:
    start_time = datetime.utcnow()

  end_time = start_time + timedelta(days=5)  # Check for the next 5 days

  user_tz = get_timezone(city)
  try:
    user_tz = pytz.timezone(user_tz)
  except pytz.UnknownTimeZoneError:
    return "Invalid timezone provided"

  headers = {
      'Authorization': f'Bearer {access_token}',
      'Content-Type': 'application/json'
  }
  params = {
      "staffIds": ["b940fb3b-06f3-44b4-b1b2-5998ec790c2a"],
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
  time_slots = response.json()['value'][0]['availabilityItems']

  current_date = datetime.now(user_tz).date()
  available_slots = []

  for slot in time_slots:
    # Convert the UTC datetime strings to datetime objects as naive
    start_dt_naive = datetime.fromisoformat(slot['startDateTime']['dateTime'])
    end_dt_naive = datetime.fromisoformat(slot['endDateTime']['dateTime'])

    # Localize the datetime objects to UTC and then convert to user's timezone
    start_dt_user_tz = pytz.utc.localize(start_dt_naive).astimezone(user_tz)
    end_dt_user_tz = pytz.utc.localize(end_dt_naive).astimezone(user_tz)

    # Update the slot's dateTime and timeZone fields to reflect the converted times
    slot['startDateTime']['dateTime'] = start_dt_user_tz.isoformat()
    slot['startDateTime']['timeZone'] = user_tz.zone
    slot['endDateTime']['dateTime'] = end_dt_user_tz.isoformat()
    slot['endDateTime']['timeZone'] = user_tz.zone

    # Filter slots that are available and not on the current date
    if slot['status'] == 'available' and start_dt_user_tz.date(
    ) != current_date:
      available_slots.append({
          'dayOfWeek': start_dt_user_tz.strftime('%A'),
          'date': start_dt_user_tz.strftime('%d-%b-%Y'),
          'startTime': start_dt_user_tz.strftime('%I:%M %p'),
          'endTime': end_dt_user_tz.strftime('%I:%M %p'),
          'timeZone': user_tz.zone
      })

  return available_slots


# In[5]:

from dateutil import parser

from dateutil import parser
# Function to check if input time is within the range

from datetime import datetime, timedelta
import pytz


def is_within_time_slots(input_time, input_timezone, time_slots):
  input_tz = pytz.timezone(input_timezone)
  input_dt_naive = datetime.strptime(input_time, '%Y-%m-%d %H:%M:%S')
  input_dt = input_tz.localize(input_dt_naive)

  print(f"Input datetime: {input_dt}")

  for slot in time_slots:
    slot_date = slot['date']
    slot_start_time = slot['startTime']
    slot_end_time = slot['endTime']

    slot_start_dt_str = f"{slot_date} {slot_start_time}"
    slot_end_dt_str = f"{slot_date} {slot_end_time}"

    # Try to parse the date and time strings using different formats
    try:
      slot_start_dt_naive = datetime.strptime(slot_start_dt_str,
                                              '%d-%b-%Y %I:%M %p')
      slot_end_dt_naive = datetime.strptime(slot_end_dt_str,
                                            '%d-%b-%Y %I:%M %p')
    except ValueError:
      try:
        slot_start_dt_naive = datetime.strptime(slot_start_dt_str,
                                                '%d/%m/%Y %I:%M %p')
        slot_end_dt_naive = datetime.strptime(slot_end_dt_str,
                                              '%d/%m/%Y %I:%M %p')
      except ValueError as e:
        print(f"Error parsing date and time: {e}")
        continue

    slot_tz = pytz.timezone(slot['timeZone'])
    slot_start_dt = slot_tz.localize(slot_start_dt_naive)
    slot_end_dt = slot_tz.localize(slot_end_dt_naive)

    slot_start_dt_local = slot_start_dt.astimezone(input_tz)
    slot_end_dt_local = slot_end_dt.astimezone(input_tz)

    print(f"Slot start: {slot_start_dt_local}, Slot end: {slot_end_dt_local}")

    if slot_start_dt_local <= input_dt < slot_end_dt_local - timedelta(
        minutes=29):
      return True

  return False


def prepare_datetime(input_time_str, timezone_str='UTC'):
  # Parse the input string into a datetime object
  input_time = parser.parse(input_time_str)

  # If timezone handling is needed, attach the specified timezone
  timezone = pytz.timezone(timezone_str)
  input_time = input_time.replace(
      tzinfo=None)  # First remove any existing tzinfo
  input_time = timezone.localize(
      input_time)  # Now localize to the specified timezone

  return input_time


from pytz import timezone


def book_appointment(name, email, phone, note, time, time_zone, address=None):
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

  start_time = (tz.normalize(tz.localize(start_time)).astimezone(
      pytz.utc)).isoformat()
  end_time = (tz.normalize(tz.localize(end_time)).astimezone(
      pytz.utc)).isoformat()
  #print(start_time,"  ", end_time )
  headers = {
      'Authorization': f'Bearer {access_token}',
      'Content-Type': 'application/json'
  }
  params = {
      "@odata.type":
      "#microsoft.graph.bookingAppointment",
      "customerTimeZone":
      time_zone,
      "smsNotificationsEnabled":
      False,
      "endDateTime": {
          "@odata.type": "#microsoft.graph.dateTimeTimeZone",
          "dateTime": end_time,
          "timeZone": "UTC"
      },
      "isLocationOnline":
      online,
      "optOutOfCustomerEmail":
      False,
      "anonymousJoinWebUrl":
      None,
      "postBuffer":
      "PT15M",
      "preBuffer":
      "PT0M",
      "price":
      0.0,
      "priceType@odata.type":
      "#microsoft.graph.bookingPriceType",
      "priceType":
      "free",
      "customerNotes":
      "Check this note ",
      "reminders@odata.type":
      "#Collection(microsoft.graph.bookingReminder)",
      "serviceId":
      service_id,
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
      "serviceName":
      "Discovery Meeting",
      "serviceNotes":
      "Meet with Hiqsense to understand your business needs",
      "staffMemberIds": [staff_id],
      "startDateTime": {
          "@odata.type": "#microsoft.graph.dateTimeTimeZone",
          "dateTime": start_time,
          "timeZone": "UTC"
      },
      "maximumAttendeesCount":
      1,
      "filledAttendeesCount":
      1,
      "customers@odata.type":
      "#Collection(microsoft.graph.bookingCustomerInformation)",
      "customers": [{
          "@odata.type": "#microsoft.graph.bookingCustomerInformation",
          "customerId": "",
          "name": name,
          "emailAddress": email,
          "phone": phone,
          "notes": "This is the customer Note",
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
          "timeZone": time_zone,
      }]
  }

  response = requests.post(url, headers=headers, json=params)
  response.raise_for_status()
  response = response.json()

  return response


# In[6]:


@tool
def book_meeting(email: str = None,
                 name: str = None,
                 phone: str = None,
                 note: Optional[str] = None,
                 start_date_time: str = None,
                 time_zone: str = None,
                 address: Optional[str] = None,
                 confirmation=False) -> dict:
  """
    Use this tool to book a meeting, get name, email, phone , start date and time of the meeting, the user timezone, address
    and any note the user would like to provide for the meeting.
    Args:
        email (str): The email of the user. Defaults to None.
        name (str): The name of the user. Defaults to None.
        phone (str): The phone number of the user. Defaults to None.
        start_date_time (str) : The date and time of the meeting in string format , you need to convert to a format 
        acceptable by python datetime function
        time_zone (str) : The user time zone, after receiving it convert it to a format acceptable by pytz
        note (Optional[str]): The note the user would like to leave for the company to prepare for the meeting. Defaults to None.
        address (Optional[str]): The address of the customer
        confirmation(boolean) : Default to False, always False until the user confirm all details.
    Don't adjust the start_date_time yourself, confirm all details with the user before booking.     
    """

  if not name:
    raise ValueError("Name is required.")

  elif not email:
    raise ValueError("Email is required.")

  elif not phone:
    raise ValueError("Phone is required.")
  elif not time_zone:
    raise ValueError("Timezone is required.")

  elif not (is_within_time_slots(
      start_date_time, time_zone,
      get_staff_availability({
          "timezone": time_zone,
          "start_time": start_date_time
      }))):
    raise ValueError(
        "Return this message to user: The meeting start time must fall within the designated time slots, and at least 30 minutes before the end of each slot."
    )
  elif not confirmation:
    error_message = f'Return this to user: To proceed with the booking please confirm the following details: Email:{email},Name:{name} , Phone: {phone} , Time: {start_date_time},Time Zone: {time_zone}'
    raise ValueError(error_message)

  else:
    response = book_appointment(name, email, phone, note, start_date_time,
                                time_zone, address)

  return response
