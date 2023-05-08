import requests
import re
from grepgithub import Hits, fetch_grep_app
import time
import random
from crawlab import save_item
from datetime import datetime


SOURCEGRAPH = "Sourcegraph"
GREPAPP = "Grep.app"

def extract_onion_addresses(text):
    onion_address_pattern = re.compile(r'[a-z2-7]{55}d\.onion')
    matches = re.findall(onion_address_pattern, text)
    return set(matches)

def search_sourcegraph(domain_name):
    headers =   {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
    url = f"https://sourcegraph.com/search/stream?q=context%3Aglobal%20{domain_name}%20count%3A2000%20fork%3Ayes%20&v=V3&t=standard&sm=0&dl=0&dk=html&dc=1&display=1500&cm=t"
    response = requests.get(url, headers=headers)
    addresses = extract_onion_addresses(response.text)
    onions = {}
    for address in addresses:
        onions[address] = "Sourcegraph"
    return onions

def search_grepapp(domain_name):
    next_page, hits, count = fetch_grep_app(page=1, query="d.onion")
    
    while next_page and next_page < 101:    # Does not paginate after 100
        time.sleep(random.uniform(1, 2))
        next_page, page_hits, _ = fetch_grep_app(page=next_page, query="d.onion")
        hits.merge(page_hits)
    print()

    onion_addresses = {}
    for repo, path_data in hits.hits.items():
        for path, lines in path_data.items():
            for line_num, line in lines.items():
                for address in extract_onion_addresses(line):
                    if address not in onion_addresses.keys():
                        onion_addresses[address] = set()
                    onion_addresses[address].add(repo)
    
    onions = {}
    for onion, repos in onion_addresses.items():
        repos = list(repos)
        repos_string = repos[0]
        if len(repos) > 1:
            for repo in repos[1:]:
                repos_string =  repos_string + ', ' + repo
        repos_string = 'Grep.app (' + repos_string + ')'
        onions[onion] = repos_string

    return onions


for source in [GREPAPP, SOURCEGRAPH]:

    print(f"Discovering onions in {source} ...\n")

    if source == SOURCEGRAPH:
        addresses = search_sourcegraph("d.onion")
    elif source == GREPAPP:
        addresses = search_grepapp("d.onion")
    
    for onion, advertiser in addresses.items():
        print(onion, advertiser)
        today = datetime.today().timestamp()                
        save_item({
            'advertiser': advertiser,
            'onion': onion,
            'timestamp': today
        })
        

    print()
    print(f"Discovered [{len(addresses)}] in {source}!!!\n")
    
    print()
    print("#####################################################")
    print()