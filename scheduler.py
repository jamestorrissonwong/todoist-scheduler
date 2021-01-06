import sys
import json
from todoist.api import TodoistAPI

import datetime
import string

import todoist_integration
import google_calendar_integration
import parse_sort

def main():

    api = todoist_integration.todoist()

    try: 
        api.sync()
    except todoist.api.SyncError:
        print('Failed to sync\n')
        exit

    todoist_integration.todoist_parent_child(api)

    to_be_scheduled = parse_sort.parse_due(api)

    priority_lists = parse_sort.priority(to_be_scheduled)

    google_service = google_calendar_integration.cal_auth()

    google_calendar_integration.clear_cal(google_service)
    
    (free_list, key_order) = google_calendar_integration.get_free_blocks(google_service)

    print(priority_lists, free_list)

    events = parse_sort.make_schedule(api, priority_lists, free_list, key_order)

    google_calendar_integration.add_events(events, google_service)



if __name__ == "__main__":
    main()

