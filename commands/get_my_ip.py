import requests

def ip():
    url = "https://ipinfo.io/ip"
    return requests.get(url).text