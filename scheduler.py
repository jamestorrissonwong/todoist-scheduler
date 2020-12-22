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

    # print(api.state['projects'])
    # print(api.state['items'])

    to_be_scheduled = parse_sort.parse_due(api)

    # for item in to_be_scheduled:
    #   print(item)

    # priority_lists = parse_sort.priority(to_be_scheduled)

    google_service = google_calendar_integration.cal_auth()
    
    # free_list = get_free_blocks(google_service)

    # events = make_schedule(priority_lists, free_list)

    # google_calendar_integration.add_events(events)



if __name__ == "__main__":
    main()

