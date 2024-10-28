from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
import uvicorn
import requests
import json

app = FastAPI()

with open("known_vpn.json", "r") as f:
    known_vpn = json.load(f)

with open("vpnapi.token", "r") as f:
    API_KEY = f.read().strip()



@app.get("/", response_class=FileResponse)
async def read_root(request: Request):

    return FileResponse("index.html")

@app.get("/is_vpn", response_class=JSONResponse)
async def is_vpn(ip: str):

    if ip in known_vpn:
        return {"is_vpn": True}

    url = f"https://vpnapi.io/api/{ip}?key={API_KEY}"
    response = requests.get(url)

    data = response.json()

    # if (data.security.vpn || data.security.proxy || data.security.tor || data.security.relay)
    if data["security"]["vpn"] or data["security"]["proxy"] or data["security"]["tor"] or data["security"]["relay"]:
        known_vpn.append(ip)
        with open("known_vpn.json", "w") as f:
            json.dump(known_vpn, f)

        return {"is_vpn": True}
    else:
        return {"is_vpn": False}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
