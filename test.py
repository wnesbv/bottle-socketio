from urllib.parse import urlparse
i = urlparse("http://127.0.0.1:8080/").path
print(i)
