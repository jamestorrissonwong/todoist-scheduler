from todoist.api import TodoistAPI


def todoist():

    try: 
        with open("todoist_api_token.txt", "rt") as api_token_file:
            api_token = api_token_file.read()
    except:
        print('Failed to get API token from file\n')
        exit

    api = TodoistAPI(api_token)
    
    return api


def todoist_parent_child(api):
    parent_due = []

    for i in api.state['items']:
        if (i['due'] != None):
            parent_due.append((i['id'], i['due']))

    for i in api.state['items']:
        if ((i['due'] == None) & (i['parent_id'] != None)):
            for (pid, due_date) in parent_due:
                if (i['parent_id'] == pid):
                    item = api.items.get_by_id(i['id'])
                    item.update(due=due_date)
                    api.commit()
                    break

    return