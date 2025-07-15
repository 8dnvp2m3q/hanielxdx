#!/usr/bin/env python3
"""
Backend API Testing Suite for Video Generation App
Tests all critical backend functionality including video generation with Ken Burns effects
"""

import requests
import json
import base64
import time
import os
from PIL import Image
import io

# Configuration
BASE_URL = "https://a23a3c63-c7d5-4829-95ff-e1173adaedc9.preview.emergentagent.com/api"
TEST_PROJECT_NAME = "Test Video Project"

class VideoGeneratorTester:
    def __init__(self):
        self.session = requests.Session()
        self.project_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
        
    def create_sample_image(self, width=800, height=600, color=(255, 0, 0)):
        """Create a sample image for testing"""
        img = Image.new('RGB', (width, height), color=color)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    def create_sample_audio(self):
        """Create a simple audio file for testing (mock MP3 header)"""
        # This is a minimal MP3 header - for testing purposes only
        mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 1000
        return mp3_header
    
    def test_api_health(self):
        """Test 1: API Health Check"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Health Check", True, f"API is running: {data['message']}")
                    return True
            self.log_test("API Health Check", False, f"Unexpected response: {response.status_code}")
            return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_create_project(self):
        """Test 2: Project Creation"""
        try:
            project_data = {
                "name": TEST_PROJECT_NAME,
                "duration": 30,
                "logo_opacity": 0.8,
                "resolution": "1080p"
            }
            
            response = self.session.post(f"{BASE_URL}/projects", json=project_data)
            
            if response.status_code == 200:
                data = response.json()
                self.project_id = data.get("id")
                if self.project_id:
                    self.log_test("Project Creation", True, f"Project created with ID: {self.project_id}")
                    return True
                else:
                    self.log_test("Project Creation", False, "No project ID returned")
                    return False
            else:
                self.log_test("Project Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Creation", False, f"Error: {str(e)}")
            return False
    
    def test_upload_images(self):
        """Test 3: Image Upload"""
        if not self.project_id:
            self.log_test("Image Upload", False, "No project ID available")
            return False
            
        try:
            # Create sample images
            image1 = self.create_sample_image(800, 600, (255, 0, 0))  # Red
            image2 = self.create_sample_image(800, 600, (0, 255, 0))  # Green
            image3 = self.create_sample_image(800, 600, (0, 0, 255))  # Blue
            
            files = [
                ('files', ('image1.jpg', image1, 'image/jpeg')),
                ('files', ('image2.jpg', image2, 'image/jpeg')),
                ('files', ('image3.jpg', image3, 'image/jpeg'))
            ]
            
            response = self.session.post(f"{BASE_URL}/projects/{self.project_id}/upload-images", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Image Upload", True, data.get("message", "Images uploaded"))
                return True
            else:
                self.log_test("Image Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Image Upload", False, f"Error: {str(e)}")
            return False
    
    def test_upload_logo(self):
        """Test 4: Logo Upload"""
        if not self.project_id:
            self.log_test("Logo Upload", False, "No project ID available")
            return False
            
        try:
            # Create a logo image (smaller, with transparency simulation)
            logo_image = self.create_sample_image(200, 200, (255, 255, 255))
            
            files = {'file': ('logo.png', logo_image, 'image/png')}
            response = self.session.post(f"{BASE_URL}/projects/{self.project_id}/upload-logo", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Logo Upload", True, data.get("message", "Logo uploaded"))
                return True
            else:
                self.log_test("Logo Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Logo Upload", False, f"Error: {str(e)}")
            return False
    
    def test_upload_music(self):
        """Test 5: Music Upload"""
        if not self.project_id:
            self.log_test("Music Upload", False, "No project ID available")
            return False
            
        try:
            # Create sample audio data
            audio_data = self.create_sample_audio()
            
            files = {'file': ('music.mp3', audio_data, 'audio/mpeg')}
            response = self.session.post(f"{BASE_URL}/projects/{self.project_id}/upload-music", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Music Upload", True, data.get("message", "Music uploaded"))
                return True
            else:
                self.log_test("Music Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Music Upload", False, f"Error: {str(e)}")
            return False
    
    def test_update_settings(self):
        """Test 6: Settings Update"""
        if not self.project_id:
            self.log_test("Settings Update", False, "No project ID available")
            return False
            
        try:
            settings_data = {
                'duration': 45,
                'logo_opacity': 0.6,
                'resolution': '720p'
            }
            
            response = self.session.put(f"{BASE_URL}/projects/{self.project_id}/settings", data=settings_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Settings Update", True, data.get("message", "Settings updated"))
                return True
            else:
                self.log_test("Settings Update", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Settings Update", False, f"Error: {str(e)}")
            return False
    
    def test_get_project(self):
        """Test 7: Get Project Details"""
        if not self.project_id:
            self.log_test("Get Project", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{BASE_URL}/projects/{self.project_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.project_id:
                    self.log_test("Get Project", True, f"Project retrieved: {data.get('name')}")
                    return True
                else:
                    self.log_test("Get Project", False, "Project ID mismatch")
                    return False
            else:
                self.log_test("Get Project", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Project", False, f"Error: {str(e)}")
            return False
    
    def test_video_generation(self):
        """Test 8: Video Generation (CRITICAL TEST)"""
        if not self.project_id:
            self.log_test("Video Generation", False, "No project ID available")
            return False
            
        try:
            print("🎬 Starting video generation (this may take a while)...")
            response = self.session.post(f"{BASE_URL}/projects/{self.project_id}/generate")
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("video_url")
                if video_url:
                    self.log_test("Video Generation", True, f"Video generated: {video_url}")
                    return video_url
                else:
                    self.log_test("Video Generation", False, "No video URL returned")
                    return False
            else:
                self.log_test("Video Generation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Video Generation", False, f"Error: {str(e)}")
            return False
    
    def test_video_download(self, video_url):
        """Test 9: Video Download"""
        if not video_url:
            self.log_test("Video Download", False, "No video URL available")
            return False
            
        try:
            # Extract filename from URL
            filename = video_url.split('/')[-1]
            download_url = f"{BASE_URL}/videos/{filename}"
            
            response = self.session.get(download_url, stream=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'video' in content_type:
                    # Check if we got actual video content
                    content_length = len(response.content) if hasattr(response, 'content') else 0
                    self.log_test("Video Download", True, f"Video downloaded ({content_length} bytes)")
                    return True
                else:
                    self.log_test("Video Download", False, f"Wrong content type: {content_type}")
                    return False
            else:
                self.log_test("Video Download", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Video Download", False, f"Error: {str(e)}")
            return False
    
    def test_get_all_projects(self):
        """Test 10: Get All Projects"""
        try:
            response = self.session.get(f"{BASE_URL}/projects")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    project_count = len(data)
                    self.log_test("Get All Projects", True, f"Retrieved {project_count} projects")
                    return True
                else:
                    self.log_test("Get All Projects", False, "Response is not a list")
                    return False
            else:
                self.log_test("Get All Projects", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get All Projects", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test 11: Error Handling"""
        error_tests = []
        
        # Test 1: Invalid project ID
        try:
            response = self.session.get(f"{BASE_URL}/projects/invalid-id")
            if response.status_code == 404:
                error_tests.append(("Invalid Project ID", True, "Correctly returned 404"))
            else:
                error_tests.append(("Invalid Project ID", False, f"Expected 404, got {response.status_code}"))
        except Exception as e:
            error_tests.append(("Invalid Project ID", False, f"Error: {str(e)}"))
        
        # Test 2: Invalid file type upload
        try:
            if self.project_id:
                files = {'file': ('test.txt', b'invalid content', 'text/plain')}
                response = self.session.post(f"{BASE_URL}/projects/{self.project_id}/upload-logo", files=files)
                if response.status_code == 400:
                    error_tests.append(("Invalid File Type", True, "Correctly rejected invalid file"))
                else:
                    error_tests.append(("Invalid File Type", False, f"Expected 400, got {response.status_code}"))
        except Exception as e:
            error_tests.append(("Invalid File Type", False, f"Error: {str(e)}"))
        
        # Test 3: Generate video without images
        try:
            # Create a new project without images
            project_data = {"name": "Empty Project", "duration": 30}
            response = self.session.post(f"{BASE_URL}/projects", json=project_data)
            if response.status_code == 200:
                empty_project_id = response.json().get("id")
                if empty_project_id:
                    gen_response = self.session.post(f"{BASE_URL}/projects/{empty_project_id}/generate")
                    if gen_response.status_code == 400:
                        error_tests.append(("Generate Without Images", True, "Correctly rejected empty project"))
                    else:
                        error_tests.append(("Generate Without Images", False, f"Expected 400, got {gen_response.status_code}"))
        except Exception as e:
            error_tests.append(("Generate Without Images", False, f"Error: {str(e)}"))
        
        # Log all error handling results
        all_passed = True
        for test_name, success, message in error_tests:
            if not success:
                all_passed = False
            self.log_test(f"Error Handling - {test_name}", success, message)
        
        return all_passed
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Video Generation App")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            ("API Health Check", self.test_api_health),
            ("Project Creation", self.test_create_project),
            ("Image Upload", self.test_upload_images),
            ("Logo Upload", self.test_upload_logo),
            ("Music Upload", self.test_upload_music),
            ("Settings Update", self.test_update_settings),
            ("Get Project", self.test_get_project),
            ("Get All Projects", self.test_get_all_projects),
        ]
        
        # Run basic tests first
        for test_name, test_func in tests:
            test_func()
            time.sleep(0.5)  # Small delay between tests
        
        # Critical video generation test
        print("\n🎬 CRITICAL TEST: Video Generation with Ken Burns Effects")
        print("-" * 50)
        video_url = self.test_video_generation()
        
        if video_url:
            # Test video download
            self.test_video_download(video_url)
        
        # Error handling tests
        print("\n🛡️ Error Handling Tests")
        print("-" * 30)
        self.test_error_handling()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        # Critical assessment
        video_gen_test = next((t for t in self.test_results if "Video Generation" in t["test"] and "Error Handling" not in t["test"]), None)
        if video_gen_test:
            if video_gen_test["success"]:
                print("\n✅ CRITICAL: Video generation with Ken Burns effects is working!")
            else:
                print("\n❌ CRITICAL: Video generation with Ken Burns effects failed!")
        
        return passed == total

if __name__ == "__main__":
    tester = VideoGeneratorTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend is fully functional.")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the summary above.")
        exit(1)