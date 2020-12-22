import sys
import json
from todoist.api import TodoistAPI
import datetime
import string

def parse_due(api):

    today = datetime.datetime.now()
    print(today.isocalendar())

    today_year, today_week, today_weekday = today.isocalendar()

    dated = []
    scheduable = []

    for item in api.state['items']:
        item_data = item.data
        due_date = item_data["due"]
        if (due_date == None):
            continue
        else:
            # print(item_data)
            ymd = due_date["date"].split('-', 3)
            date_sep_time = ymd[2].split('T', -1)
            this_date = datetime.datetime(int(ymd[0]), int(ymd[1]), int(date_sep_time[0]))
            dated.append((this_date, item_data))
            
    for task in dated:
        (date, data) = task
        date_year, date_week, date_weekday = date.isocalendar()

        if (abs(date_year - today_year) <= 1):
            if (today_week == date_week): 
                if (date_weekday < today_weekday):
                    
                    scheduable.append((date, data, True))
                else:
                    
                    scheduable.append((date, data, False))
            elif (date_week < today_week):
                
                scheduable.append((date, data, True))

    return scheduable

def priority(item_list):


    return 0