import requests
import re
import random
import time
from crawlab import save_item
from datetime import datetime

ALIENVAULT = "AlienVault"
REPOSITORIES = "Suspicious/Scam/Malware repositories"


def search_repositories(urls_file):
    with open(urls_file, 'r') as f:
        urls = f.readlines()
        
    # Compile the regex pattern
    pattern = re.compile(r'[a-z2-7]{55}d\.onion')
    onion_domains = set()
    
    for i, url in enumerate(urls):
        # Clean the URL and remove newline characters
        url = url.strip()
        
        print(f"Processing URL {i + 1} of {len(urls)}: {url}")
        
        # Send a GET request to the URL
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Error while processing URL {i + 1}: {response.status_code}")
            continue
        
        # Extract the list of onion domains
        matches = re.findall(pattern, response.text)
        
        # Add the extracted domains to the set
        onion_domains |= set(matches)
    
    return list(onion_domains)


def search_alienvault():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}    
    pattern = r"[a-z2-7]{55}d\.onion"
    onion_domains = set()
    pages = 0

    for modified in ["-modified", "modified"]:
        next_url = f"https://otx.alienvault.com/otxapi/indicators/?type=domain,hostname,URI,URL&include_inactive=1&sort={modified}&q=d.onion"

        while next_url:
            print(f"Analyzing page {pages}...")
            pages+=1
            response = requests.get(next_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for result in data["results"]:
                    indicator = result["indicator"]
                    match = re.search(pattern, indicator)
                    if match:
                        onion_domains.add(match.group())

                print(f"Found {len(onion_domains)} onions so far")

                next_url = data.get("next")
                if next_url:
                    sleep_time = random.uniform(1, 3)
                    #print(f"Sleeping for {sleep_time} seconds before next request")
                    time.sleep(sleep_time)
                    # print(f"Next URL: {next_url}")
            else:
                print("Finished!\n")
                break

    print("Finished getting onion domains")
    return list(onion_domains)


for source in [REPOSITORIES,ALIENVAULT]:

    if source == REPOSITORIES:
        onion_domains = search_repositories('iocs.txt')
    elif source == ALIENVAULT:
        onion_domains = search_alienvault()
    
    print(f"\nUnique onion domains: {len(onion_domains)} in {source}\n")

    for onion in onion_domains:
        # print(f"{onion} IOC Repositories ({source})")
        today = datetime.today().timestamp() 
        save_item({
            'advertiser': source,
            'onion': onion,
            'timestamp': today
        })


    print(f"\nUnique onion domains: {len(onion_domains)} in {source}\n")

    print("######################################################\n")