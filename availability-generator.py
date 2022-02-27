import datetime
import os.path
import calendar
from time import time
import numpy as np
import logging

from math import floor
import itertools
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(encoding='utf-8', level=logging.INFO)        
                
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
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
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
    def __init__(self,events=None):
        self.events=events
        self.cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        self.today = datetime.datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
        
        self.days = itertools.chain(self.cal.itermonthdates(self.today.year,self.today.month),
                          self.cal.itermonthdates(self.today.year,self.today.month+1))

        self.start_hour = 9 # Start day at 9AM
        self.end_hour = 19  # End day at 7PM
        self.timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        self.get_availability()
    
    def event_datetime(self,event_num,type='start'):
        assert type in ('start','end')
        try: 
            return datetime.datetime.fromisoformat(self.events[event_num][type]['dateTime'])
        except KeyError:
            logging.warning("Skipped event %s" % self.events[event_num][type])
            return datetime.datetime.fromisoformat(self.events[event_num][type]['date'])

    def pad_minutes(self,dt: datetime.time, pad: int):
        new_mins = dt.minute+pad
        return dt.replace(hour = (dt.hour+floor(new_mins/60)),
                          minute = new_mins%60)
            
    def get_availability(self,pad=30):
        i=0
        k=0
        num_events = len(self.events)
        hours_per_day = self.end_hour - self.start_hour
        num_intervals = 4*hours_per_day
        days_list = [datetime.datetime.combine(day,datetime.datetime.min.time()) for day in self.days]
        
        isBusy = np.zeros(shape=(len(days_list),num_intervals),dtype=bool)
        logging.info("number of 15 min intervals: %d, Total hours per day: %d" % (num_intervals,hours_per_day)) 
        for day in days_list:  
            # Day from 9a-7p
            start_of_day = day.replace(hour=self.start_hour,minute=0,second=0)            
            end_of_day = day.replace(hour=self.end_hour,minute=0,second=0)
            start = start_of_day
            # Iterate through events until we reach events for the next day
            while self.event_datetime(i).date() == day.date() and day.date() >= self.today.date() and i<(num_events-1):
                if start == start_of_day:
                    # Only print the day of the week and date for the day's first event
                    print(day.strftime("%A %B %d,%Y"))

                # Get the time the event starts and the time it ends
                event_start = self.event_datetime(i,type='start')
                event_end = self.event_datetime(i,type='end')

                logging.info((event_start.strftime("%I:%M%p"),
                          event_end.strftime("%I:%M%p"),
                          str(self.timezone)))
                
                start_hour = (event_start.timestamp() - start_of_day.timestamp())/3600
                end_hour = (event_end.timestamp() - start_of_day.timestamp())/3600
                
                ix_start = int(4*start_hour)
                ix_end = int(min(4*end_hour,len(isBusy[0,:])-1))
                logging.info("ix_start: %d, ix_end: %d" % (ix_start,ix_end))
                
                for n in range(ix_start,ix_end):
                    isBusy[k,n] = 1

                print(isBusy[k,:])
                    
                if event_start.timestamp() > start.timestamp():
                    print(start.strftime('\t%I:%M%p'),"-",
                          event_start.strftime('%I:%M%p'),
                          self.timezone)
                    # Set the day's start_time to the event's ending, padded with padding_mins
                    start = event_end                   
                i+=1
            k+=1 
        return
    
if __name__ == '__main__':
    gcal = gcal()
    mycal = personal_calendar(gcal.get_events())

    