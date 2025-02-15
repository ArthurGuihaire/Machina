import requests
response = requests.get("https://api64.ipify.org?format=text")
public_ip = response.text
print(f"IP Address: {public_ip}")