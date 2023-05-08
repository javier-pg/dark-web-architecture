import json
import os
import re
import time
import uuid
import bs4
import requests
import random
import warnings
from bs4 import MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning, module='bs4')

class Hits:

    def __init__(self):
        self.mark_start_placeholder = str(uuid.uuid4())
        self.mark_end_placeholder = str(uuid.uuid4())
        self.hits = {}

    def _parse_snippet(self, snippet):
        matches = {}
        soup = bs4.BeautifulSoup(snippet, 'lxml')
        for tr in soup.select('tr'):
            line_num = tr.select("div.lineno")[0].text.strip()
            line = tr.select("pre")[0].decode_contents()
            if "<mark" not in line:
                continue
            else:
                line = re.sub(r'<mark[^<]*>',  self.mark_start_placeholder, line)
                line = line.replace("</mark>", self.mark_end_placeholder)
                line = bs4.BeautifulSoup(line, 'lxml').text
                line = line.replace(self.mark_start_placeholder, "")
                line = line.replace(self.mark_end_placeholder, "")
                matches[line_num] = line
        return matches

    def add_hit(self, repo, path, snippet):
        if repo not in self.hits:
            self.hits[repo] = {}
        if path not in self.hits[repo]:
            self.hits[repo][path] = {}
        # Parse snippet
        for line_num, line in self._parse_snippet(snippet).items():
            self.hits[repo][path][line_num] = line

    def merge(self, hits2):
        for hit_repo, path_data in hits2.hits.items():
            if hit_repo not in self.hits:
                self.hits[hit_repo] = {}
            for path, lines in path_data.items():
                if path not in self.hits[hit_repo]:
                    self.hits[hit_repo][path] = {}
                for line_num, line in lines.items():
                    self.hits[hit_repo][path][line_num] = line


def fail(error_msg):
    print("Error: {}\033[0m".format(error_msg))
    exit(1)

def fetch_grep_app(page, query):
    url = "https://grep.app/api/search"
    params = {
        'q': query,
        'page': page,
        'case': 'true'
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        fail("HTTP {} {}".format(response.status_code, url))
    data = response.json()
    count = data['facets']['count']
    hits = Hits()
    for hit_data in data['hits']['hits']:
        repo = hit_data['repo']['raw']
        path = hit_data['path']['raw']
        snippet = hit_data['content']['snippet']
        hits.add_hit(repo, path, snippet)

    print(f"Page {page}", end="; ", flush=True)

    if count > 10 * page:
        return page + 1, hits, count
        #return 101, hits, count
    else:
        return None, hits, count