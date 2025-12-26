from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os, shutil, json, asyncio

from generate import generate_certificates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

for folder in ["static", "templates", "temp"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(
    csv_file: UploadFile = File(...),
    image_file: UploadFile = File(...),
    font_file: UploadFile = File(...),
    column: str = Form(...),
    pos_x: str = Form(...),
    pos_y: str = Form(...),
    font_size: str = Form(...),
    text_color: str = Form(...)
):
    if os.path.exists("temp"): shutil.rmtree("temp")
    os.makedirs("temp/fonts", exist_ok=True)
    os.makedirs("temp/output", exist_ok=True)

    c_p, i_p, f_p = "temp/data.csv", "temp/template.png", "temp/fonts/font.ttf"

    with open(c_p, "wb") as f: shutil.copyfileobj(csv_file.file, f)
    with open(i_p, "wb") as f: shutil.copyfileobj(image_file.file, f)
    with open(f_p, "wb") as f: shutil.copyfileobj(font_file.file, f)

    async def progress_stream():
        for status in generate_certificates(c_p, i_p, f_p, column, pos_x, pos_y, font_size, text_color):
            yield f"data: {json.dumps(status)}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(progress_stream(), media_type="text/event-stream")

@app.get("/download")
async def download():
    return FileResponse("temp/certificates.zip", filename="certificates.zip")