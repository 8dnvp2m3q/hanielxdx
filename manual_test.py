#!/usr/bin/env python3
"""
Manual Backend Test - Test individual components
"""

import requests
import json
import base64
import time
from PIL import Image
import io
import os

def create_sample_image(width=800, height=600, color=(255, 0, 0)):
    """Create a sample image for testing"""
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()

def create_sample_audio():
    """Create a simple audio file for testing"""
    # Simple MP3-like header for testing
    return b'\xff\xfb\x90\x00' + b'\x00' * 1000

def test_backend_manually():
    """Manual test of backend functionality"""
    print("🔧 Manual Backend Testing")
    print("=" * 40)
    
    # Test 1: Check if we can import the server modules
    print("1. Testing server imports...")
    try:
        import sys
        sys.path.append('/app/backend')
        from server import VideoProject, VideoProjectCreate
        print("✅ Server modules imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Test MongoDB connection
    print("\n2. Testing MongoDB connection...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_mongo():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            result = await client.admin.command('ping')
            client.close()
            return result
        
        result = asyncio.run(test_mongo())
        print(f"✅ MongoDB connection successful: {result}")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    
    # Test 3: Test FFmpeg availability
    print("\n3. Testing FFmpeg availability...")
    try:
        import ffmpeg
        # Try to get FFmpeg version
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg available: {version_line}")
        else:
            print("❌ FFmpeg not working properly")
            return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in system")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        return False
    
    # Test 4: Test image processing
    print("\n4. Testing image processing...")
    try:
        # Create a test image
        test_image = create_sample_image(800, 600, (255, 0, 0))
        
        # Test base64 encoding/decoding
        b64_image = base64.b64encode(test_image).decode('utf-8')
        decoded_image = base64.b64decode(b64_image)
        
        # Test PIL processing
        with Image.open(io.BytesIO(decoded_image)) as img:
            width, height = img.size
            print(f"✅ Image processing successful: {width}x{height}")
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        return False
    
    # Test 5: Test video project model
    print("\n5. Testing video project model...")
    try:
        project_data = {
            "name": "Test Project",
            "duration": 30,
            "logo_opacity": 0.8,
            "resolution": "1080p"
        }
        
        project = VideoProject(**project_data)
        print(f"✅ Video project model works: {project.name} (ID: {project.id})")
    except Exception as e:
        print(f"❌ Video project model failed: {e}")
        return False
    
    # Test 6: Test Ken Burns function (without actual execution)
    print("\n6. Testing Ken Burns function structure...")
    try:
        from server import create_ken_burns_effect, create_video_from_images
        print("✅ Ken Burns functions imported successfully")
        
        # Test if the function signature is correct
        import inspect
        sig = inspect.signature(create_ken_burns_effect)
        params = list(sig.parameters.keys())
        expected_params = ['image_path', 'output_path', 'duration']
        
        if all(param in params for param in expected_params):
            print("✅ Ken Burns function signature is correct")
        else:
            print(f"❌ Ken Burns function signature mismatch. Got: {params}")
            return False
            
    except Exception as e:
        print(f"❌ Ken Burns function test failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("📊 MANUAL TEST SUMMARY")
    print("=" * 40)
    print("✅ All core components are working!")
    print("✅ MongoDB connection: OK")
    print("✅ FFmpeg availability: OK") 
    print("✅ Image processing: OK")
    print("✅ Video project models: OK")
    print("✅ Ken Burns functions: OK")
    
    return True

def test_api_endpoints_with_curl():
    """Test API endpoints using curl commands"""
    print("\n🌐 Testing API Endpoints with curl")
    print("=" * 40)
    
    base_url = "http://localhost:8001/api"
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        import subprocess
        result = subprocess.run(['curl', '-s', '-m', '10', f'{base_url}/'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and 'Video Generator API' in result.stdout:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test 2: Create project
    print("\n2. Testing project creation...")
    try:
        project_data = '{"name":"Test Project","duration":30,"logo_opacity":0.8,"resolution":"1080p"}'
        result = subprocess.run([
            'curl', '-s', '-m', '10', '-X', 'POST', 
            '-H', 'Content-Type: application/json',
            '-d', project_data,
            f'{base_url}/projects'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                project_id = response_data.get('id')
                if project_id:
                    print(f"✅ Project creation working: {project_id}")
                    return project_id
                else:
                    print(f"❌ No project ID in response: {result.stdout}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {result.stdout}")
                return False
        else:
            print(f"❌ Project creation failed: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Project creation error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Comprehensive Backend Testing")
    print("=" * 50)
    
    # Run manual component tests
    manual_success = test_backend_manually()
    
    if manual_success:
        # Run API endpoint tests
        project_id = test_api_endpoints_with_curl()
        
        if project_id:
            print(f"\n🎉 Backend is working! Core functionality verified.")
            print(f"✅ Project created with ID: {project_id}")
        else:
            print(f"\n⚠️ Core components work but API endpoints have issues.")
    else:
        print(f"\n❌ Core components have issues.")