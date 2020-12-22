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


