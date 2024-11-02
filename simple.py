from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()


@app.get("/", response_class=FileResponse)
async def read_root(request: Request):

    return FileResponse("index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)