import sys
import json
from todoist.api import TodoistAPI
import datetime
import string
from dataclasses import dataclass

@dataclass
class task_info:
    id: int
    date: datetime
    data: dict
    overdue: bool
    time: int = -1

today = datetime.datetime.now()
today_year, today_week, today_weekday = today.isocalendar()

def set_time(item_list, time_list):
    has_time = []

    for i in item_list:
        id = i.id
        for t in time_list:
            (pid, time) = t
            if (id == pid):
                i.time = time
                time_list.remove(t)
                break
        
        if (i.time != -1):
            has_time.append(i)

    return has_time


def parse_due(api):
    print(today.isocalendar())

    dated = []
    scheduable = []
    id_times = []

    for item in api.state['items']:
        item_data = item.data
        due_date = item_data["due"]
        if (due_date == None):
            continue
        else:
            ymd = due_date["date"].split('-', 3)
            date_sep_time = ymd[2].split('T', -1)
            this_date = datetime.datetime(int(ymd[0]), int(ymd[1]), int(date_sep_time[0]))
            dated.append((this_date, item_data))
            
    for task in dated:
        (date, data) = task
        date_year, date_week, date_weekday = date.isocalendar()

        id = data['id']

        content_string = data['content']
        if("!Time" in content_string):
            pid = data['parent_id']
            time = data['content'].split('!Time ', 2)
            timeint = int(time[1])
            id_times.append((pid, timeint))
            continue
            
        if (abs(date_year - today_year) <= 1):
            if (today_week == date_week): 
                if (date_weekday < today_weekday):
                    ti = task_info(id, date, data, True)
                    scheduable.append(ti)
                else:
                    ti = task_info(id, date, data, False)
                    scheduable.append(ti)
            elif (date_week < today_week):
                ti = task_info(id, date, data, True)
                scheduable.append(ti)

    scheduable = set_time(scheduable, id_times)

    return scheduable


def merge(a, b):
    sorted = []

    for i in a:
        for j in b:
            if(i.time < j.time):
                sorted.append(j)
                b.remove(j)
                continue
            else:
                sorted.append(i)
                a.remove(i)
                break

    return sorted

# sort
def sort_by_time(list):
    n = len(list)
    if ((n == 1) | (n == 0)):
        return list
    else:    
        x = int(n/2)
        y = x + 1
        l1 = list[:x]
        l2 = list[y:]

        left = sort_by_time(l1)
        right = sort_by_time(l2)

        sorted = merge(left, right)
        #print(sorted)
        return sorted


def priority(item_list):

    priority_dict = {
        "Overdue":[[],[],[],[]],
        "1":[[],[],[],[]],
        "2":[[],[],[],[]],
        "3":[[],[],[],[]],
        "4":[[],[],[],[]],
        "5":[[],[],[],[]],
        "6":[[],[],[],[]],
        "7":[[],[],[],[]]
    }

    # Sort by date and priority
    for item in item_list:
        id = item.id
        date = item.date
        data = item.data
        overdue = item.overdue
        time = item.time 

        if overdue:
            di = priority_dict["Overdue"]
            p = abs(data["priority"] - 4)
            dip = di[p]
            dip.append(item)
            priority_dict["Overdue"] = di
        else:
            date_year, date_week, date_weekday = date.isocalendar()
            di = priority_dict[str(date_weekday)]
            p = abs(int(data["priority"]) - 4)
            dip = di[p]
            dip.append(item)
            priority_dict[str(date_weekday)] = di

    # Within each priority sort by amount of time
    for dict_key in priority_dict:
        dict_entry = priority_dict[dict_key]
        for i in range(0, 4):
            pl = dict_entry[i]
            pl = sort_by_time(pl)
            dict_entry[i] = pl

    p_list = []

    # Fold the dicts back into a single list
    for dict_key in ["Overdue", "1", "2", "3", "4", "5", "6", "7"]:
        dict_entry = priority_dict[dict_key]
        p_list = p_list + dict_entry[0] + dict_entry[1] + dict_entry[2] + dict_entry[3]
            
    return p_list


def make_schedule(api, item_list, calendar_list, key_order):

    event_list = []
    print(len(item_list))

    for i in item_list:
        time = i.time
        data = i.data
        pid = data['project_id']
        project = api.projects.get_by_id(pid)
        project_name = project['name']
        desc = data['content']
        time_delta = datetime.timedelta(minutes=time)

        for j in key_order:
            day = calendar_list[j]
            if (len(day) == 0):
                continue
            (free_start, free_end) = day.pop()
            free_delta = free_end - free_start

            if (time_delta < free_delta):
                new_start = free_start + time_delta
                day.insert(0, (new_start, free_end))
                event_list.append((project_name, desc, free_start.isoformat(), new_start.isoformat()))
                break
            elif (time_delta > free_delta):
                time_delta = time_delta - free_delta
                event_list.append((project_name, desc, free_start.isoformat(), free_end.isoformat())) 
            else:
                event_list.append((project_name, desc, free_start.isoformat(), free_end.isoformat())) 
                break

    return event_list