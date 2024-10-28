from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
import uvicorn
import requests
import json
import bs4

app = FastAPI()

with open("./cache/known_vpn.json", "r") as f:
    known_vpn_cache = json.load(f)

with open("./cache/web_autocomplete.json", "r") as f:
    web_autocomplete_cache = json.load(f)

with open("vpnapi.token", "r") as f:
    API_KEY = f.read().strip()



@app.get("/", response_class=FileResponse)
async def read_root(request: Request):

    return FileResponse("index.html")

@app.get("/is_vpn", response_class=JSONResponse)
async def is_vpn(ip: str):

    if ip in known_vpn_cache:
        return {"is_vpn": True}

    url = f"https://vpnapi.io/api/{ip}?key={API_KEY}"
    response = requests.get(url)

    data = response.json()

    # if (data.security.vpn || data.security.proxy || data.security.tor || data.security.relay)
    if data["security"]["vpn"] or data["security"]["proxy"] or data["security"]["tor"] or data["security"]["relay"]:
        known_vpn_cache.append(ip)
        with open("/cache/known_vpn.json", "w") as f:
            json.dump(known_vpn_cache, f)

        return {"is_vpn": True}
    else:
        return {"is_vpn": False}

@app.get("/web_autocomplete", response_class=JSONResponse)
async def web_autocomplete(q: str):

    if q in web_autocomplete_cache.keys():
        return web_autocomplete_cache[q]


    url = f"https://duckduckgo.com/ac/?q={q}&kl=wt-wt"
    response = requests.get(url)
    data = response.json()

    web_autocomplete_cache[q] = data

    with open("./cache/web_autocomplete.json", "w") as f:
        json.dump(web_autocomplete_cache, f)

    return data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
