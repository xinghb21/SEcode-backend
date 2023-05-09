import requests

# Set the request parameters
url = 'http::/127.0.0.1:8000/asset/post'

for i in range(10, 10000):
    re = requests.post(url, data={})