from requests import Response




def __HTTP_response_handler(response: Response):
    if response.status_code == 200:
            return response
    elif response.status_code == 429:
        
        return
    elif response.status_code == 503:
        print(f"Service unavailable: {status_code}")
        return
    elif response.status_code == 401:
        print(f"Unauthorized: {status_code}")
        return
    else:
        print(f"Unknown error: {status_code}")
        return

def steamWebApiHandler():
    pass

