from datetime import datetime,time,timezone

import os.path
import calendar
import numpy as np
import logging


from math import floor
import itertools
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
            
class gcal:
    def __init__(self,credentials_file="credentials.json",save_token=True,num_events = 40):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.credentials = None
        self.num_events = num_events
        if os.path.exists('token.json'):
            self.credentials = Credentials.from_authorized_user_file('token.json', self.SCOPES)   
        # If there are no (valid) credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json',self.SCOPES)
                self.credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
            if save_token:
                with open('token.json', 'w') as token:
                    token.write(self.credentials.to_json())
                
    def get_events(self):
        try:
            service = build('calendar', 'v3', credentials=self.credentials)
            # Call the Calendar API
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=self.num_events, singleEvents=True,
                                              orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                logging.info('No upcoming events found.')
            return events
        except HttpError as error:
            logging.error('An error occurred: %s' % error)


class personal_calendar():
    def __init__(self,events_input=None):
        self.events = [e for e in events_input if 'dateTime' in e['start'].keys()]
        self.cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        self.today = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
        
        days_iter = itertools.chain(self.cal.itermonthdates(self.today.year,self.today.month),
                          self.cal.itermonthdates(self.today.year,self.today.month+1))
        self.days=[]
        for day in days_iter: 
            if day not in self.days and day >= self.today.date():
                self.days.append(day)
                
        self.days = [datetime.combine(day,datetime.min.time()) for day in self.days]    
                
                
        self.start_hour = 9 # Start day at 9AM
        self.end_hour = 19  # End day at 7PM
        self.hours_per_day = self.end_hour - self.start_hour
        self.num_intervals = 4*self.hours_per_day
        self.timezone = datetime.now(timezone.utc).astimezone().tzinfo
        self.get_availability()
    
    def event_datetime(self,event_num,type='start'):
        if type in ('start','end') and 'dateTime' in self.events[event_num][type].keys():
            return datetime.fromisoformat(self.events[event_num][type]['dateTime'])
            
                

    def pad_minutes(self,dt: datetime, pad: int):
        return datetime.fromtimestamp(dt.timestamp()+pad*60)
            
    def get_availability(self,pad=15):
        i=0
        num_events = len(self.events)
        
        for k in range(len(self.days)):
            first_event_of_day = True  
            start_of_day = self.days[k].replace(hour=self.start_hour,minute=0,second=0)
                      
            start = start_of_day
            if self.event_datetime(i).date()> self.days[k].date(): 
                pass
            else:
                while(self.event_datetime(i).date() == self.days[k].date() and i<(num_events-1)):
                    event_start =self.event_datetime(i,type='start')
                    event_end = self.event_datetime(i,type='end')
                    
                    logging.info((event_start.strftime("%I:%M%p"),
                            event_end.strftime("%I:%M%p"),
                            str(self.timezone)))
                    
                    if first_event_of_day: 
                        print(self.days[k].strftime("%A %x"))
                        first_event_of_day=False

                    event_start = self.pad_minutes(event_start,-1*pad)    
                    if event_start.time() > start.time():
                        print(start.strftime("\t%I:%M%p"),"-",event_start.strftime("%I:%M%p"))
                        
                    start = event_end                    
                    i+=1

                
                                

                
                 
                    
            
            
            
        
        
if __name__ == '__main__':
    gcal = gcal()
    mycal = personal_calendar(gcal.get_events())

    