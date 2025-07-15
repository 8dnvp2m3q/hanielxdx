from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import ffmpeg
import base64
import json
import asyncio
from PIL import Image
import io
import shutil
import tempfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create directories for file storage
UPLOAD_DIR = ROOT_DIR / "uploads"
OUTPUT_DIR = ROOT_DIR / "outputs"
MUSIC_DIR = ROOT_DIR / "music"

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, MUSIC_DIR]:
    dir_path.mkdir(exist_ok=True)

# Define Models
class VideoProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    images: List[str] = []  # base64 encoded images
    duration: int = 30  # seconds
    music_file: Optional[str] = None
    logo_file: Optional[str] = None
    logo_opacity: float = 0.8
    resolution: str = "1080p"  # 720p or 1080p
    created_at: datetime = Field(default_factory=datetime.utcnow)
    video_url: Optional[str] = None
    status: str = "draft"  # draft, processing, completed, failed

class VideoProjectCreate(BaseModel):
    name: str
    duration: int = 30
    logo_opacity: float = 0.8
    resolution: str = "1080p"

class VideoGenerationRequest(BaseModel):
    project_id: str

def create_ken_burns_effect(image_path: str, output_path: str, duration: float, zoom_start: float = 1.0, zoom_end: float = 1.2, pan_x: float = 0, pan_y: float = 0):
    """Create Ken Burns effect for a single image"""
    try:
        # Get image dimensions
        with Image.open(image_path) as img:
            width, height = img.size
        
        # Create vertical 9:16 aspect ratio (1080x1920 for 1080p)
        target_width = 1080
        target_height = 1920
        
        # Calculate zoom and pan effects
        zoom_filter = f"scale={int(width*zoom_start)}:{int(height*zoom_start)}"
        pan_filter = f"crop={target_width}:{target_height}:{pan_x}:{pan_y}"
        
        # Create FFmpeg command for Ken Burns effect
        (
            ffmpeg
            .input(image_path, loop=1, t=duration)
            .filter('scale', target_width, target_height)
            .filter('zoompan', z=f'min(zoom+0.0015,1.5)', d=int(duration*30), x='iw/2-(iw/zoom/2)', y='ih/2-(ih/zoom/2)', s=f'{target_width}x{target_height}')
            .output(output_path, vcodec='libx264', pix_fmt='yuv420p', r=30)
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception as e:
        print(f"Error creating Ken Burns effect: {e}")
        return False

def create_video_from_images(project: VideoProject, output_path: str):
    """Create video from images with Ken Burns effects and transitions"""
    try:
        temp_dir = tempfile.mkdtemp()
        video_clips = []
        
        # Process each image
        for i, image_b64 in enumerate(project.images):
            # Decode base64 image
            image_data = base64.b64decode(image_b64)
            image_path = os.path.join(temp_dir, f"image_{i}.jpg")
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Create video clip with Ken Burns effect
            clip_path = os.path.join(temp_dir, f"clip_{i}.mp4")
            clip_duration = project.duration / len(project.images)
            
            # Vary zoom and pan for each image
            zoom_start = 1.0 + (i * 0.1)
            zoom_end = 1.2 + (i * 0.1)
            pan_x = (i % 2) * 100  # Alternate pan direction
            pan_y = (i % 3) * 50
            
            if create_ken_burns_effect(image_path, clip_path, clip_duration, zoom_start, zoom_end, pan_x, pan_y):
                video_clips.append(clip_path)
        
        if not video_clips:
            raise Exception("No video clips created")
        
        # Concatenate clips with fade transitions
        inputs = [ffmpeg.input(clip) for clip in video_clips]
        
        if len(inputs) == 1:
            # Single clip
            stream = inputs[0]
        else:
            # Multiple clips with fade transitions
            stream = inputs[0]
            for i in range(1, len(inputs)):
                stream = ffmpeg.filter([stream, inputs[i]], 'xfade', transition='fade', duration=0.5)
        
        # Add logo overlay if provided
        if project.logo_file:
            logo_data = base64.b64decode(project.logo_file)
            logo_path = os.path.join(temp_dir, "logo.png")
            with open(logo_path, 'wb') as f:
                f.write(logo_data)
            
            # Overlay logo in bottom-right corner
            stream = ffmpeg.overlay(stream, ffmpeg.input(logo_path), x='W-w-20', y='H-h-20', eval='init')
        
        # Add background music if provided
        if project.music_file:
            music_data = base64.b64decode(project.music_file)
            music_path = os.path.join(temp_dir, "music.mp3")
            with open(music_path, 'wb') as f:
                f.write(music_data)
            
            audio = ffmpeg.input(music_path).audio
            stream = ffmpeg.output(stream, audio, output_path, vcodec='libx264', acodec='aac', pix_fmt='yuv420p')
        else:
            stream = ffmpeg.output(stream, output_path, vcodec='libx264', pix_fmt='yuv420p')
        
        # Run FFmpeg
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"Error creating video: {e}")
        return False

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Video Generator API"}

@api_router.post("/projects", response_model=VideoProject)
async def create_project(project_data: VideoProjectCreate):
    """Create a new video project"""
    project = VideoProject(**project_data.dict())
    await db.video_projects.insert_one(project.dict())
    return project

@api_router.get("/projects", response_model=List[VideoProject])
async def get_projects():
    """Get all video projects"""
    projects = await db.video_projects.find().to_list(1000)
    return [VideoProject(**project) for project in projects]

@api_router.get("/projects/{project_id}", response_model=VideoProject)
async def get_project(project_id: str):
    """Get a specific project"""
    project = await db.video_projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return VideoProject(**project)

@api_router.post("/projects/{project_id}/upload-images")
async def upload_images(project_id: str, files: List[UploadFile] = File(...)):
    """Upload images to a project"""
    project = await db.video_projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert uploaded files to base64
    images = []
    for file in files:
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Only JPEG and PNG files are allowed")
        
        content = await file.read()
        # Resize image if too large
        with Image.open(io.BytesIO(content)) as img:
            if img.width > 1920 or img.height > 1920:
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                content = output.getvalue()
        
        b64_image = base64.b64encode(content).decode('utf-8')
        images.append(b64_image)
    
    # Update project with images
    await db.video_projects.update_one(
        {"id": project_id},
        {"$set": {"images": images}}
    )
    
    return {"message": f"Uploaded {len(images)} images successfully"}

@api_router.post("/projects/{project_id}/upload-logo")
async def upload_logo(project_id: str, file: UploadFile = File(...)):
    """Upload logo to a project"""
    project = await db.video_projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only PNG and JPEG files are allowed for logo")
    
    content = await file.read()
    b64_logo = base64.b64encode(content).decode('utf-8')
    
    await db.video_projects.update_one(
        {"id": project_id},
        {"$set": {"logo_file": b64_logo}}
    )
    
    return {"message": "Logo uploaded successfully"}

@api_router.post("/projects/{project_id}/upload-music")
async def upload_music(project_id: str, file: UploadFile = File(...)):
    """Upload background music to a project"""
    project = await db.video_projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if file.content_type not in ["audio/mpeg", "audio/mp3", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Only MP3 and WAV files are allowed")
    
    content = await file.read()
    b64_music = base64.b64encode(content).decode('utf-8')
    
    await db.video_projects.update_one(
        {"id": project_id},
        {"$set": {"music_file": b64_music}}
    )
    
    return {"message": "Music uploaded successfully"}

@api_router.post("/projects/{project_id}/generate")
async def generate_video(project_id: str):
    """Generate video from project"""
    project_data = await db.video_projects.find_one({"id": project_id})
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = VideoProject(**project_data)
    
    if not project.images:
        raise HTTPException(status_code=400, detail="No images uploaded")
    
    # Update status to processing
    await db.video_projects.update_one(
        {"id": project_id},
        {"$set": {"status": "processing"}}
    )
    
    # Generate video
    output_filename = f"{project_id}_{project.resolution}.mp4"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        success = create_video_from_images(project, str(output_path))
        
        if success:
            # Update project with video URL
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {
                    "video_url": f"/api/videos/{output_filename}",
                    "status": "completed"
                }}
            )
            return {"message": "Video generated successfully", "video_url": f"/api/videos/{output_filename}"}
        else:
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"status": "failed"}}
            )
            raise HTTPException(status_code=500, detail="Video generation failed")
            
    except Exception as e:
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@api_router.get("/videos/{filename}")
async def get_video(filename: str):
    """Download generated video"""
    video_path = OUTPUT_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(video_path, media_type="video/mp4", filename=filename)

@api_router.put("/projects/{project_id}/settings")
async def update_project_settings(project_id: str, duration: int = Form(...), logo_opacity: float = Form(...), resolution: str = Form(...)):
    """Update project settings"""
    project = await db.video_projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.video_projects.update_one(
        {"id": project_id},
        {"$set": {
            "duration": duration,
            "logo_opacity": logo_opacity,
            "resolution": resolution
        }}
    )
    
    return {"message": "Settings updated successfully"}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    result = await db.video_projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Clean up video file if exists
    video_files = list(OUTPUT_DIR.glob(f"{project_id}_*.mp4"))
    for video_file in video_files:
        video_file.unlink(missing_ok=True)
    
    return {"message": "Project deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()