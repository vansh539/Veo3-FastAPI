import os
import time
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from fastapi.staticfiles import StaticFiles

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY env var is not set")

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class ReelRequest(BaseModel):
    prompt: str

class ReelResponse(BaseModel):
    video_url: str

@app.post("/generate-reel", response_model=ReelResponse)
def generate_reel(req: ReelRequest):
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=req.prompt,
    )

    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)

    generated_video = operation.response.generated_videos[0]

    # Download the video bytes
    video_bytes = client.files.download(file=generated_video.video)

    # Ensure static directory exists
    os.makedirs("static", exist_ok=True)

    file_path = "static/reel_output.mp4"
    with open(file_path, "wb") as f:
        f.write(video_bytes)

    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
    public_url = f"{base_url}/{file_path}"

    return {"video_url": public_url}
