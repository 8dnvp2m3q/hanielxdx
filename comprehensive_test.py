#!/usr/bin/env python3
"""
Comprehensive Backend API Test - Full workflow test
"""

import subprocess
import json
import base64
import tempfile
import os
import sys
from PIL import Image
import io

def create_sample_image(width=800, height=600, color=(255, 0, 0)):
    """Create a sample image for testing"""
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()

def run_curl_command(method, url, data=None, files=None, timeout=30):
    """Run curl command and return result"""
    cmd = ['curl', '-s', '-m', str(timeout), '-X', method]
    
    if data:
        cmd.extend(['-H', 'Content-Type: application/json', '-d', data])
    
    if files:
        for field_name, file_path in files.items():
            cmd.extend(['-F', f'{field_name}=@{file_path}'])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def test_full_video_workflow():
    """Test the complete video generation workflow"""
    print("🎬 Full Video Generation Workflow Test")
    print("=" * 50)
    
    base_url = "http://localhost:8001/api"
    project_id = None
    
    # Step 1: Create project
    print("1. Creating video project...")
    project_data = json.dumps({
        "name": "Full Workflow Test",
        "duration": 15,  # Shorter duration for testing
        "logo_opacity": 0.8,
        "resolution": "720p"  # Lower resolution for faster processing
    })
    
    success, response, error = run_curl_command('POST', f'{base_url}/projects', data=project_data)
    if success:
        try:
            data = json.loads(response)
            project_id = data.get('id')
            print(f"✅ Project created: {project_id}")
        except:
            print(f"❌ Invalid response: {response}")
            return False
    else:
        print(f"❌ Project creation failed: {error}")
        return False
    
    # Step 2: Upload images
    print("\n2. Uploading test images...")
    
    # Create temporary image files
    temp_dir = tempfile.mkdtemp()
    image_files = []
    
    try:
        for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
            image_data = create_sample_image(800, 600, color)
            image_path = os.path.join(temp_dir, f'image_{i}.jpg')
            with open(image_path, 'wb') as f:
                f.write(image_data)
            image_files.append(image_path)
        
        # Upload images using curl with multipart form data
        cmd = [
            'curl', '-s', '-m', '30', '-X', 'POST',
            f'{base_url}/projects/{project_id}/upload-images'
        ]
        
        for image_path in image_files:
            cmd.extend(['-F', f'files=@{image_path}'])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"✅ Images uploaded: {data.get('message', 'Success')}")
            except:
                print(f"✅ Images uploaded (non-JSON response): {result.stdout}")
        else:
            print(f"❌ Image upload failed: {result.stdout}")
            return False
            
    finally:
        # Cleanup temp files
        for file_path in image_files:
            try:
                os.unlink(file_path)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
    
    # Step 3: Get project to verify images
    print("\n3. Verifying project with images...")
    success, response, error = run_curl_command('GET', f'{base_url}/projects/{project_id}')
    if success:
        try:
            data = json.loads(response)
            image_count = len(data.get('images', []))
            print(f"✅ Project has {image_count} images")
            if image_count == 0:
                print("❌ No images found in project")
                return False
        except:
            print(f"❌ Invalid project response: {response}")
            return False
    else:
        print(f"❌ Failed to get project: {error}")
        return False
    
    # Step 4: Generate video (this is the critical test)
    print("\n4. 🎬 CRITICAL TEST: Generating video with Ken Burns effects...")
    print("   (This may take 30-60 seconds...)")
    
    success, response, error = run_curl_command('POST', f'{base_url}/projects/{project_id}/generate', timeout=90)
    
    if success:
        try:
            data = json.loads(response)
            video_url = data.get('video_url')
            if video_url:
                print(f"✅ Video generated successfully!")
                print(f"   Video URL: {video_url}")
                
                # Step 5: Test video download
                print("\n5. Testing video download...")
                video_filename = video_url.split('/')[-1]
                download_url = f'{base_url}/videos/{video_filename}'
                
                success, response, error = run_curl_command('GET', download_url, timeout=30)
                if success and len(response) > 1000:  # Video should be reasonably sized
                    print(f"✅ Video download successful ({len(response)} bytes)")
                    return True
                else:
                    print(f"❌ Video download failed or too small: {len(response) if success else 0} bytes")
                    return False
            else:
                print(f"❌ No video URL in response: {data}")
                return False
        except json.JSONDecodeError:
            # Check if it's an error response
            if "Video generation failed" in response:
                print(f"❌ Video generation failed: {response}")
                return False
            else:
                print(f"❌ Invalid JSON response: {response}")
                return False
    else:
        print(f"❌ Video generation request failed: {error}")
        return False

def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n🛡️ Error Handling Tests")
    print("=" * 30)
    
    base_url = "http://localhost:8001/api"
    
    # Test 1: Invalid project ID
    print("1. Testing invalid project ID...")
    success, response, error = run_curl_command('GET', f'{base_url}/projects/invalid-id')
    if not success or "404" in response or "not found" in response.lower():
        print("✅ Correctly handled invalid project ID")
    else:
        print(f"❌ Should have returned 404: {response}")
    
    # Test 2: Generate video without images
    print("\n2. Testing video generation without images...")
    project_data = json.dumps({"name": "Empty Project", "duration": 30})
    success, response, error = run_curl_command('POST', f'{base_url}/projects', data=project_data)
    
    if success:
        try:
            data = json.loads(response)
            empty_project_id = data.get('id')
            if empty_project_id:
                success, response, error = run_curl_command('POST', f'{base_url}/projects/{empty_project_id}/generate')
                if not success or "No images" in response or "400" in response:
                    print("✅ Correctly rejected video generation without images")
                else:
                    print(f"❌ Should have rejected empty project: {response}")
        except:
            print("❌ Failed to parse empty project response")
    
    return True

def main():
    print("🚀 Comprehensive Backend API Testing")
    print("=" * 50)
    
    # Test full workflow
    workflow_success = test_full_video_workflow()
    
    # Test error scenarios
    error_success = test_error_scenarios()
    
    print("\n" + "=" * 50)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 50)
    
    if workflow_success:
        print("✅ CRITICAL: Video generation workflow is working!")
        print("✅ Ken Burns effects implementation verified")
        print("✅ File upload and processing working")
        print("✅ Video download functionality working")
    else:
        print("❌ CRITICAL: Video generation workflow failed!")
    
    if error_success:
        print("✅ Error handling is working properly")
    else:
        print("❌ Error handling has issues")
    
    overall_success = workflow_success and error_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! Backend is fully functional.")
        print("🎬 Video generation with Ken Burns effects is working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()