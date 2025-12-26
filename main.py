from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os, shutil, json, asyncio

from generate import generate_certificates

app = FastAPI()

# Render handles relative paths well, but absolute paths are even safer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Local 'temp' folder works on Render
BASE_TEMP = os.path.join(BASE_DIR, "temp")

# Initial folder setup
os.makedirs(BASE_TEMP, exist_ok=True)

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
    # Clean previous run
    if os.path.exists(BASE_TEMP): 
        shutil.rmtree(BASE_TEMP)
    
    os.makedirs(os.path.join(BASE_TEMP, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(BASE_TEMP, "output"), exist_ok=True)

    c_p = os.path.join(BASE_TEMP, "data.csv")
    i_p = os.path.join(BASE_TEMP, "template.png")
    f_p = os.path.join(BASE_TEMP, "fonts", "font.ttf")

    with open(c_p, "wb") as f: shutil.copyfileobj(csv_file.file, f)
    with open(i_p, "wb") as f: shutil.copyfileobj(image_file.file, f)
    with open(f_p, "wb") as f: shutil.copyfileobj(font_file.file, f)

    async def progress_stream():
        # Ensure generate_certificates is using the 9th argument for the base path
        for status in generate_certificates(c_p, i_p, f_p, column, pos_x, pos_y, font_size, text_color, BASE_TEMP):
            yield f"data: {json.dumps(status)}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(progress_stream(), media_type="text/event-stream")

@app.get("/download")
async def download():
    zip_path = os.path.join(BASE_TEMP, "certificates.zip")
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename="certificates.zip")
    return {"error": "File not found. Please generate again."}
