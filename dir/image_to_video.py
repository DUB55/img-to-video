from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import List

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # Specific origin instead of wildcard
    allow_credentials=True,
    allow_methods=["OPTIONS", "POST", "GET"],
    allow_headers=["Content-Type", "Origin", "Accept"],
    max_age=86400
)

def create_frame(image: Image.Image, text: str, frame_number: int, total_frames: int) -> Image.Image:
    frame = image.copy()
    draw = ImageDraw.Draw(frame)
    width, height = frame.size
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = height - 60
    
    outline_color = "black"
    text_color = "white"
    outline_width = 2
    
    for adj in range(-outline_width, outline_width + 1):
        for adj2 in range(-outline_width, outline_width + 1):
            if adj != 0 or adj2 != 0:
                draw.text((text_x + adj, text_y + adj2), text, font=font, fill=outline_color)
    
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    return frame

@app.post("/api/image-to-video")
async def create_video(
    image: UploadFile = File(...),
    text: str = Form(...),
    duration: int = Form(5)
):
    try:
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        fps = 30
        total_frames = duration * fps
        frames: List[Image.Image] = []
        
        # Generate frames
        for i in range(total_frames):
            frame = create_frame(img, text, i, total_frames)
            frames.append(frame)
        
        # Create GIF
        output_buffer = io.BytesIO()
        frames[0].save(
            output_buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=1000/fps,
            loop=0
        )
        
        output_buffer.seek(0)
        gif_base64 = base64.b64encode(output_buffer.getvalue()).decode()
        
        return JSONResponse({
            "message": "Animation created successfully",
            "video_data": f"data:image/gif;base64,{gif_base64}"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
