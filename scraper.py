"""
How did I calculate the New Moons?
Step 1 - calculate astronomical new moon. (This is in UTC+0)
Step 2 - calculate the next sunset in Jerusalem (This is in UTC+3)
Step 3 - if the sunset is at least 18 hours after the new moon the day of the sunset is the first of the month
Step 4 - else, the first of the month will be the next day
"""

# 7/7, 6/7, 5/9, 4/9

# https://astropixels.com/ephemeris/phasescat/phases2001.html
# https://aa.usno.navy.mil/calculated/rstt/year?ID=AA&year=2024&task=0&lat=31.7683&lon=35.2137&label=Jerusalem&tz=0&tz_sign=-1&submit=Get+Data
import requests
import time
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

start = time.time()
successes = 0
failures = 0
# 6157 PIDs

request_url = "https://astropixels.com/ephemeris/phasescat/phases2001.html"
r = requests.get(request_url, verify=False)
if  r.url == request_url and r.status_code == 200:
        with open(f"raw/new_moon/20XX.html", "w") as f:
            f.write(r.text)

print(r.status_code)

for i in range(2024, 2100): # Current Number of  PIDs
    request_url = f"https://aa.usno.navy.mil/calculated/rstt/year?ID=AA&year={i}&task=0&lat=31.7683&lon=35.2137&label=Jerusalem&tz=0&tz_sign=-1&submit=Get+Data"
    r = requests.get(request_url, verify=False)
    if  r.url == request_url and r.status_code == 200:
        with open(f"raw/sunset/{i}.html", "w") as f:
            f.write(r.text)
        successes += 1
    else:
        with open("failures.txt", "a") as f:
            f.write(str(i+1))
            f.write("\n")
            failures += 1
    r.close()
    
    if i % 10 == 0:
        percent = 100*((successes+failures)+1)/76
        print("~"*100)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        print(f"Elapsed time: {time.time() - start}")
        print(f"{i+1} URLs have been scraped!")
        print(f"We are now {percent:.2f}% done!")
        print(f"Number of successes: {successes}")
        print(f"Number of failures: {failures}")
    time.sleep(1.5)

print("~"*100)
print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
print(f"Completed in {time.time() - start}")
print(f"{i} URLs have been scraped!")

print(f"Number of successes: {successes}")
print(f"Number of failures: {failures}")
percent = 100*successes/76
print(f"{percent:.2f}% of calls have succeeded!")