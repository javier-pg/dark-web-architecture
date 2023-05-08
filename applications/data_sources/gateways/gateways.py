import requests
from bs4 import BeautifulSoup
import re
#from fake_useragent import UserAgent
import time
import random
from crawlab import save_item
from datetime import datetime
from duckduckgo_search import ddg

GOOGLE = 'Google'
DUCKDUCKGO = 'DuckDuckGo'

def google_search(query):
    headers =   {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
    start = 0
    urls = []
    next_page = True

    while next_page:

        try:
            response = requests.get(
                f"https://www.google.com/search?q=site:{query}&start={start}",
                headers=headers)

            # Parse the HTML content
            soup = BeautifulSoup(response.content, "html.parser")
            # print(soup)

            # Find all the URLs in the search results
            try:
                urls += [a["href"] for a in soup.select("a")]
            except Exception as error:
                print("Error in getting Google results: ", error)
                return urls

            next_page = bool(soup.find_all("a", {"class": "nBDE1b G5eFlf"}))
            print(f"Page {start//10}", end="; ", flush=True)
            start += 10
            time.sleep(random.uniform(20, 60))
        
        except requests.exceptions.RequestException as error:
            print("Error in request: ", error)
            return urls
    
    print()
    return urls


def duckduckgo_search(query):

    urls = []

    try:
        results = ddg(
            f"site:{query}",
            region='wt-wt',
            safesearch='Off',
            time=None,
            max_results=200)
    except Exception as error:
        print("Error in duckduckgo_search: ", error)
        return urls

    if results is not None:
        for result in results:
            urls.append(result['href'])
    
    return urls
    
       

# Define the query and regular expression
url_pattern = r'[a-z2-7]{55}d\.'

# Get random user-agent
# ua = UserAgent()

# Cookie for consent yes
cookies = {"CONSENT": "YES+cb.20210720-07-p0.en+FX+410"}

# Open the file containing the queries
with open("queries.txt", "r") as f:

    # Read the lines of the file
    queries = f.readlines()

    # remove the newline character
    queries = [q.strip() for q in queries]

    # Iterate over the gateways
    for query in queries:

        # Iterage over the search engines
        for search_engine in [DUCKDUCKGO]:
        
        
            print(f"Gathering onion services from gateway [{query}] in {search_engine}...\n")
            urls = []
            if search_engine == GOOGLE:
                urls = google_search(query)
            elif search_engine == DUCKDUCKGO:
                urls = duckduckgo_search(query)

            if urls:
                # Filter the URLs based on the regular expression of onion service
                filtered_urls = [re.search(url_pattern, url).group(0) for url in urls if re.search(url_pattern, url)]

                if filtered_urls:
                    # Print the filtered URLs
                    #print("Results for query: ",query)
                    onions=[]
                    for url in set(filtered_urls):
                        onions.append(url+"onion")


                    if onions is not None:
                        onions = set(onions)

                        print(f"\nDiscovered [{len(onions)}] unique onions using gateway {query} in [{search_engine}]!")
                        print()

                        for onion in onions:
                            print(onion)
                            today = datetime.today().timestamp()
                            
                            save_item({
                                'advertiser': f"{search_engine} ({query})",
                                'onion': onion,
                                'timestamp': today
                            })
                        print()
                        
        time.sleep(random.uniform(10, 20))  
        print()
        print("================================================================")
        print()