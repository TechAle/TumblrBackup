import requests

def makeRequest(url, method="GET", header=None):
    if header is None:
        header = []
    return requests.request(
        url=url,
        method=method,
        headers=header
    )


