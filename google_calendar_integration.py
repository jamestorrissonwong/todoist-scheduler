from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime as dt
from datetime import datetime

# All of these calls to the Google API were adapted from Google Calendar API documentation


SCOPES = ['https://www.googleapis.com/auth/calendar']

def cal_auth():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service

def take_min_max(a, b):
    (s1, e1) = a
    (s2, e2) = b

    start = -1
    end = -1

    if (s1 < s2):
        start = s1 
    else:
        start = s2

    if (e1 < e2):
        end = e2
    else:
        end = e1

    return (start, end)

def check_overlap(blocks):
    n = len(blocks)

    for i in range(0,(n-1)):
        for j in range((i+1),n):
            (s1, e1) = blocks[i]
            (s2, e2) = blocks[j]
            if(((s2 < e1) & (e2 >= e1)) | ((s1 < e2) & (e1 >= e2))):
                return (True, blocks[i], blocks[j])

    return (False, None, None)

def coalesce_blocks(blocks):
    coalesced = []
    key_order = []
    
    (has_overlap, t1, t2) = check_overlap(blocks)

    while(has_overlap):
        (s1, e1) = t1
        (s2, e2) = t2

        blocks.remove(t1)
        blocks.remove(t2)

        if(s2 < e1) :
            new_block =  (s1, e2)
            coalesced.append(new_block)
        else:
            new_block = (s2, e1)
            coalesced.append(new_block)

        (has_overlap, t1, t2) = check_overlap(blocks)

    coalesced += blocks
    
    busy_by_day = {}

    for i in range(0, 7):
        d = datetime.now() + (dt.timedelta(days=i))
        key = d.strftime("%d")
        busy_by_day[key] = []
        key_order.append(key)

    for block in coalesced:
        (s,e) = block
        key = s.strftime("%d")
        free_list = busy_by_day[key]
        free_list.append((s,e))
        busy_by_day[key] = free_list

    return (busy_by_day, key_order)

def merge(a, b):
    sorted = []

    for i in a:
        for j in b:
            (x, y) = i
            (x2, y2) = j
            if(x < x2):
                sorted.append(j)
                b.remove(j)
                continue
            else:
                sorted.append(i)
                a.remove(i)
                break

    return sorted

# sort
def sort_busy(list):
    n = len(list)
    if ((n == 1) | (n == 0)):
        return list
    else:    
        x = int(n/2)
        y = x + 1
        l1 = list[:x]
        l2 = list[y:]

        left = sort_busy(l1)
        right = sort_busy(l2)

        sorted = merge(left, right)
        #print(sorted)
        return sorted

def free_from_busy(blocks):
    free_time = {}

    for day in blocks:
        blocks[day] = sort_busy(blocks[day])

    start = (datetime.now()).replace(tzinfo=dt.timezone(dt.timedelta(hours=-8)))
    end = start.replace(hour=22, minute=0, second=0)

    for i in blocks:
        tmp = []
        
        if (len(blocks[i]) == 0):
            tmp.append((start, end))
            free_time[i] = tmp
            start = start.replace(day=(start.day + 1), hour=8, minute=0, second=0)
            end = start.replace(hour=22, minute=0, second=0)
            continue

        for (s, e) in (blocks[i]):
            if (s < start):
                start = e
                continue
            elif (e > end):
                break
            else:
                tmp.append((start, s))
                start = e
                
        print(tmp)
        free_time[i] = tmp
        start = start.replace(day=(start.day + 1), hour=8, minute=0, second=0)
        end = start.replace(hour=22, minute=0, second=0)
        
    return free_time


def get_free_blocks(service):

    start = datetime.now().replace(microsecond=0) 
    delta = dt.timedelta(days=7)
    end = start + delta
    start = start.isoformat() + "-08:00"
    end = end.isoformat() + "-08:00"

    print(start)
    print(end)

    ids = []

    page_token = None
    while True:
        calendar_list = service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            calendar_dict = {'id': calendar_list_entry['id']}
            ids.append(calendar_dict)
        
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    
    request = {
        "timeMin": start,
        "timeMax": end,
        "timeZone": "PST",
        "items": ids
    }

    free_busy_info = service.freebusy().query(body=request).execute()
    
    busy_dicts = []

    for i in free_busy_info['calendars']:
        calendars = (free_busy_info['calendars'])[i]
        busy_dicts += calendars['busy']

    busy_blocks = []

    for i in busy_dicts:
        start = i['start']
        end = i['end']
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        busy_blocks.append((start_date, end_date))

    
    (coalesced_blocks, key_order) = coalesce_blocks(busy_blocks)

    print(len(coalesced_blocks))

    free_blocks = free_from_busy(coalesced_blocks)

    return (free_blocks, key_order)


def add_events(event_list, service):

    calendar_name = 'Todoist Scheduler'    
    calendar_id = None

    page_token = None
    while True:
        calendar_list = service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if (calendar_list_entry['summary'] == calendar_name):
                calendar_id = calendar_list_entry['id']
                break
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    print(calendar_id)
    print('len')
    print(len(event_list))
    
    if (calendar_id == None):
        todoist_calendar_json = {
            'summary':'Todoist Scheduler',
        }
        todoist_calendar = service.calendars().insert(body=todoist_calendar_json).execute()
        print(todoist_calendar['id'])
        calendar_id = todoist_calendar['id']

    for event in event_list: 
        (name, desc, start, end) = event

        event_json = {
            'summary':name,
            'description':desc,
            'start':{
                'dateTime':start
            },
            'end':{
                'dateTime':end
            }
        }

        service.events().insert(calendarId=calendar_id, body=event_json).execute()

    return 0


def clear_cal(service):

    delete_list = []

    calendar_id = None
    calendar_name = 'Todoist Scheduler'

    while True:
        calendar_list = service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if (calendar_list_entry['summary'] == calendar_name):
                calendar_id = calendar_list_entry['id']
                break
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    if (calendar_id == None):
        return

    start = datetime.now().replace(microsecond=0) 
    delta = dt.timedelta(days=7)
    end = start + delta
    start = start.isoformat() + "-08:00"
    end = end.isoformat() + "-08:00"

    print(start)
    print(end)

    request = {
        "timeMin": start,
        "timeZone": "PST",
        "calendarId": calendar_id
    }

    page_token = None
    while True:
        events = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
        for event in events['items']:
            print(event)
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
        page_token = events.get('nextPageToken')
        if not page_token:
            break
