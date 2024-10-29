from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
import uvicorn
import requests
import json
import bs4
import time

app = FastAPI()

with open("./cache/known_vpn.json", "r") as f:
    known_vpn_cache = json.load(f)

def add_to_known_vpn_cache(ip):
    known_vpn_cache.append(ip)
    with open("./cache/known_vpn.json", "w") as f:
        json.dump(known_vpn_cache, f)



with open("./cache/web_autocomplete.json", "r") as f:
    web_autocomplete_cache = json.load(f)

def add_to_web_autocomplete_cache(q, data):
    web_autocomplete_cache[q] = data
    with open("./cache/web_autocomplete.json", "w") as f:
        json.dump(web_autocomplete_cache, f)



with open("vpnapi.token", "r") as f:
    API_KEY = f.read().strip()



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
        add_to_known_vpn_cache(ip)

        t_end_add = time.time()
        print(f"Add to cache took {(t_end_add - t_end_request) * 1000:.2f} milliseconds")


        return {"is_vpn": True}
    else:
        return {"is_vpn": False}

@app.get("/web_autocomplete", response_class=JSONResponse)
async def web_autocomplete(q: str):

    if q in web_autocomplete_cache.keys():
        return web_autocomplete_cache[q]

    data_out = []

    # Wikipedia articles

    headers = {
        "User-Agent": "browser-start-page (linus@linush.org)"
    }

    t_start = time.time()

    url = f"https://api.wikimedia.org/core/v1/wikipedia/en/search/page?q={q}&limit=5"
    response = requests.get(url, headers=headers)
    data = response.json()
    # {pages:[{title: str, ...},], ...}

    for item in data["pages"]:
        data_out.append({"phrase": item["title"], "url": f"https://en.wikipedia.org/wiki/{item['title']}"})

    t_end_wikipedia = time.time()
    print(f"Wikipedia took {(t_end_wikipedia - t_start) * 1000:.2f} milliseconds")

    # duckduckgo autocomplete

    url = f"https://duckduckgo.com/ac/?q={q}&kl=wt-wt"
    response = requests.get(url)
    data = response.json()
    #[{phrase: str}, {phrase: str}, ...]

    for item in data:
        data_out.append({"phrase": item["phrase"], "url": f"https://duckduckgo.com/?q={item['phrase']}"})

    t_end_duckduckgo = time.time()
    print(f"DuckDuckGo took {(t_end_duckduckgo - t_end_wikipedia) * 1000:.2f} milliseconds")


    add_to_web_autocomplete_cache(q, data_out)

    t_end_add = time.time()
    print(f"Add to cache took {(t_end_add - t_end_duckduckgo) * 1000:.2f} milliseconds")

    return data_out


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
