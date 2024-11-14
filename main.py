from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

import plyvel
import uvicorn
import requests
import bs4
import urllib.parse
import httpx

import json
import time
import asyncio
import ctypes
import random


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


levenshtein = ctypes.CDLL("./levenshtein.so")

def levenshtein_distance(a, b):
    return levenshtein.levenshtein_distance(a.encode("utf-8"), b.encode("utf-8"))


@abstractmethod
class Cache(ABC):
    # Abstract class for a Cache that can store any arbitrary str:str key-value pairs

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

class LevelDBCache(Cache):
    def __init__(self, filename):
        self.db = plyvel.DB(filename, create_if_missing=True)
    
    def get(self, key):
        val = self.db.get(key.encode("utf-8"))
        if val is not None:
            return val.decode("utf-8")
        else:
            return None
    
    def set(self, key, value):
        self.db.put(key.encode("utf-8"), value.encode("utf-8"))

    def __contains__(self, key):
        return self.get(key) is not None

    def close(self):
        self.db.close()
    
    def __del__(self):
        self.close()


known_vpn_cache = LevelDBCache("./cache/known_vpn.ldb")

web_autocomplete_cache = LevelDBCache("./cache/web_autocomplete.ldb")


with open("vpnapi.token", "r") as f:
    API_KEY = f.read().strip()


requests.packages.urllib3.util.connection.HAS_IPV6 = False

transport = httpx.HTTPTransport(local_address="0.0.0.0")
limits = httpx.Limits(max_keepalive_connections=None, max_connections=None, keepalive_expiry=None)

google = httpx.Client(http2=True, follow_redirects=True, transport=transport, limits=limits)
google.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:109.0) Gecko/20100101 Firefox/121.0"'})


def get_random_header():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.89",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]


    headers = {
        "User-Agent": random.choice(user_agents), # Choose a user-agent at random
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.5",
        "Dnt": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    return headers

@app.get("/", response_class=FileResponse)
async def read_root(request: Request):

    return FileResponse("index.html")

@app.get("/is_vpn", response_class=JSONResponse)
async def is_vpn(ip: str):

    if ip in known_vpn_cache:
        return {"is_vpn": True}

    t_start = time.time()

    url = f"https://vpnapi.io/api/{ip}?key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    t_end_request = time.time()
    print(f"Request took {(t_end_request - t_start) * 1000:.2f} milliseconds")

    # if (data.security.vpn || data.security.proxy || data.security.tor || data.security.relay)
    if data["security"]["vpn"] or data["security"]["proxy"] or data["security"]["tor"] or data["security"]["relay"]:
        known_vpn_cache.set(ip, "1")

        t_end_add = time.time()
        print(f"Add to cache took {(t_end_add - t_end_request) * 1000:.2f} milliseconds")


        return {"is_vpn": True}
    else:
        return {"is_vpn": False}



def autocomplete_duckduckgo(q: str) -> list[dict[str, str]]:
    t_start = time.time()

    print("DuckDuckGo")

    url = f"https://duckduckgo.com/ac/?q={q}&kl=wt-wt"
    response = requests.get(url)
    data = response.json()
    #[{phrase: str}, {phrase: str}, ...]

    print(f"DuckDuckGo took {(time.time() - t_start) * 1000:.2f} milliseconds")
    print(len(data))

    return [{"phrase": item["phrase"] + "   ", "url": f"https://duckduckgo.com/?q={item['phrase']}"} for item in data]

def autocomplete_wikipedia(q: str) -> list[dict[str, str]]:
    t_start = time.time()

    print("Wikipedia")

    headers = {
        "User-Agent": "browser-start-page (linus@linush.org)"
    }

    url = f"https://api.wikimedia.org/core/v1/wikipedia/en/search/page?q={q}&limit=5"
    response = requests.get(url, headers=headers)
    data = response.json()
    # {pages:[{title: str, ...},], ...}

    print(f"Wikipedia took {(time.time() - t_start) * 1000:.2f} milliseconds")

    return [{"phrase": item["title"], "url": f"https://en.wikipedia.org/wiki/{item['title']}"} for item in data["pages"]]

def google_search(q: str) -> list[dict[str, str]]:
    t_start = time.time()

    print("Google Search")

    q = urllib.parse.quote(q)
    url = f"https://www.google.com/search?gl=us&hl=en&pws=0&gws_rd=cr&num=10&q={q}"

    response = google.get(url, headers=get_random_header())

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    
    result_divs = soup.find_all("div", {"class": "yuRUbf"})

    results = []

    for div in result_divs:
        a = div.find("a")
        title = a.find("h3").text
        url = a["href"]
        results.append({"phrase": title, "url": url})
    
    print(f"Google Search took {(time.time() - t_start) * 1000:.2f} milliseconds")
    print(len(results))

    if len(results) == 0:
        with open(f"google_error-{q}.html", "w") as f:
            f.write(response.text)

    return results

def autocomplete_minecraft_wiki(q: str) -> list[dict[str, str]]:
    t_start = time.time()

    print("Minecraft Wiki")

    results = google_search(f"site:minecraft.wiki {q}")

    print(f"Minecraft Wiki took {(time.time() - t_start) * 1000:.2f} milliseconds")
    print(len(results))

    return results

def reddit_search(q: str) -> list[dict[str, str]]:
    t_start = time.time()

    print("Reddit Search")

    results = google_search(f"site:reddit.com {q}")

    print(f"Reddit Search took {(time.time() - t_start) * 1000:.2f} milliseconds")
    print(len(results))

    return results
    



@app.get("/web_autocomplete", response_class=JSONResponse)
async def web_autocomplete(q: str):

    if q in web_autocomplete_cache:
        return json.loads(web_autocomplete_cache.get(q))

    providers = [autocomplete_duckduckgo, autocomplete_wikipedia, autocomplete_minecraft_wiki, google_search]

    loop = asyncio.get_running_loop()
    futures = []
    with ThreadPoolExecutor() as pool:
        for provider in providers:
            futures.append(loop.run_in_executor(pool, provider, q))
        
        results = await asyncio.gather(*futures)
    
    results = [item for sublist in results for item in sublist]

    # Sort the phrases by their Levenshtein distance to the query

    results.sort(key=lambda x: levenshtein_distance(x["phrase"], q))


    web_autocomplete_cache.set(q, json.dumps(results))

    return results



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
