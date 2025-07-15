import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoGenerator = () => {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [activeTab, setActiveTab] = useState('create');
  const [loading, setLoading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [projectSettings, setProjectSettings] = useState({
    duration: 30,
    logo_opacity: 0.8,
    resolution: '1080p'
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const createProject = async (name) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/projects`, {
        name,
        ...projectSettings
      });
      setCurrentProject(response.data);
      setProjects([...projects, response.data]);
      setActiveTab('edit');
    } catch (error) {
      console.error('Error creating project:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadImages = async (files) => {
    if (!currentProject) return;
    
    try {
      setLoading(true);
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      await axios.post(`${API}/projects/${currentProject.id}/upload-images`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Refresh project data
      const response = await axios.get(`${API}/projects/${currentProject.id}`);
      setCurrentProject(response.data);
      
      // Convert base64 to preview URLs
      const previews = response.data.images.map(img => `data:image/jpeg;base64,${img}`);
      setUploadedImages(previews);
    } catch (error) {
      console.error('Error uploading images:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadLogo = async (file) => {
    if (!currentProject) return;
    
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);

      await axios.post(`${API}/projects/${currentProject.id}/upload-logo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const response = await axios.get(`${API}/projects/${currentProject.id}`);
      setCurrentProject(response.data);
    } catch (error) {
      console.error('Error uploading logo:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadMusic = async (file) => {
    if (!currentProject) return;
    
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);

      await axios.post(`${API}/projects/${currentProject.id}/upload-music`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const response = await axios.get(`${API}/projects/${currentProject.id}`);
      setCurrentProject(response.data);
    } catch (error) {
      console.error('Error uploading music:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateVideo = async () => {
    if (!currentProject) return;
    
    try {
      setLoading(true);
      await axios.post(`${API}/projects/${currentProject.id}/generate`);
      
      // Refresh project data
      const response = await axios.get(`${API}/projects/${currentProject.id}`);
      setCurrentProject(response.data);
      fetchProjects();
    } catch (error) {
      console.error('Error generating video:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async () => {
    if (!currentProject) return;
    
    try {
      const formData = new FormData();
      formData.append('duration', projectSettings.duration);
      formData.append('logo_opacity', projectSettings.logo_opacity);
      formData.append('resolution', projectSettings.resolution);

      await axios.put(`${API}/projects/${currentProject.id}/settings`, formData);
      
      const response = await axios.get(`${API}/projects/${currentProject.id}`);
      setCurrentProject(response.data);
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const CreateProjectTab = () => (
    <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Create New Video Project</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Project Name</label>
          <input
            type="text"
            placeholder="Enter project name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            id="project-name"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Duration (seconds)</label>
          <input
            type="number"
            min="15"
            max="60"
            value={projectSettings.duration}
            onChange={(e) => setProjectSettings({...projectSettings, duration: parseInt(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Resolution</label>
          <select
            value={projectSettings.resolution}
            onChange={(e) => setProjectSettings({...projectSettings, resolution: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="720p">720p (HD)</option>
            <option value="1080p">1080p (Full HD)</option>
          </select>
        </div>
        
        <button
          onClick={() => {
            const name = document.getElementById('project-name').value;
            if (name.trim()) {
              createProject(name);
            }
          }}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Creating...' : 'Create Project'}
        </button>
      </div>
    </div>
  );

  const EditProjectTab = () => (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Edit Project: {currentProject?.name}</h2>
        
        {/* Image Upload */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Upload Images (2-5 images)</h3>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => uploadImages(e.target.files)}
              className="hidden"
              id="image-upload"
            />
            <label
              htmlFor="image-upload"
              className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Choose Images
            </label>
            <p className="mt-2 text-gray-600">PNG, JPG up to 10MB each</p>
          </div>
          
          {uploadedImages.length > 0 && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {uploadedImages.map((img, index) => (
                <div key={index} className="relative">
                  <img
                    src={img}
                    alt={`Preview ${index + 1}`}
                    className="w-full h-24 object-cover rounded-lg"
                  />
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Settings */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Duration (seconds)</label>
            <input
              type="number"
              min="15"
              max="60"
              value={projectSettings.duration}
              onChange={(e) => setProjectSettings({...projectSettings, duration: parseInt(e.target.value)})}
              onBlur={updateSettings}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Logo Opacity</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={projectSettings.logo_opacity}
              onChange={(e) => setProjectSettings({...projectSettings, logo_opacity: parseFloat(e.target.value)})}
              onMouseUp={updateSettings}
              className="w-full"
            />
            <span className="text-sm text-gray-600">{Math.round(projectSettings.logo_opacity * 100)}%</span>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Resolution</label>
            <select
              value={projectSettings.resolution}
              onChange={(e) => setProjectSettings({...projectSettings, resolution: e.target.value})}
              onBlur={updateSettings}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="720p">720p (HD)</option>
              <option value="1080p">1080p (Full HD)</option>
            </select>
          </div>
        </div>
        
        {/* Logo Upload */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Logo (Optional)</h3>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => e.target.files[0] && uploadLogo(e.target.files[0])}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {currentProject?.logo_file && (
            <p className="mt-2 text-green-600">✓ Logo uploaded</p>
          )}
        </div>
        
        {/* Music Upload */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Background Music (Optional)</h3>
          <input
            type="file"
            accept="audio/*"
            onChange={(e) => e.target.files[0] && uploadMusic(e.target.files[0])}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {currentProject?.music_file && (
            <p className="mt-2 text-green-600">✓ Music uploaded</p>
          )}
        </div>
        
        {/* Generate Button */}
        <div className="text-center">
          <button
            onClick={generateVideo}
            disabled={loading || !currentProject?.images?.length}
            className="bg-green-600 text-white px-8 py-3 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg font-semibold"
          >
            {loading ? 'Generating Video...' : 'Generate Video'}
          </button>
        </div>
        
        {/* Video Preview */}
        {currentProject?.video_url && (
          <div className="mt-8 text-center">
            <h3 className="text-lg font-semibold mb-4">Generated Video</h3>
            <video
              controls
              className="max-w-sm mx-auto rounded-lg shadow-lg"
              style={{ aspectRatio: '9/16' }}
            >
              <source src={`${BACKEND_URL}${currentProject.video_url}`} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            <div className="mt-4">
              <a
                href={`${BACKEND_URL}${currentProject.video_url}`}
                download
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                Download Video
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const HistoryTab = () => (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Project History</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <div key={project.id} className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-2">{project.name}</h3>
            <p className="text-gray-600 mb-2">Duration: {project.duration}s</p>
            <p className="text-gray-600 mb-2">Resolution: {project.resolution}</p>
            <p className="text-gray-600 mb-4">Status: 
              <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                project.status === 'completed' ? 'bg-green-100 text-green-800' :
                project.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                project.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {project.status}
              </span>
            </p>
            
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setCurrentProject(project);
                  setActiveTab('edit');
                  if (project.images) {
                    const previews = project.images.map(img => `data:image/jpeg;base64,${img}`);
                    setUploadedImages(previews);
                  }
                }}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
              >
                Edit
              </button>
              
              {project.video_url && (
                <a
                  href={`${BACKEND_URL}${project.video_url}`}
                  download
                  className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-colors"
                >
                  Download
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {projects.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No projects yet. Create your first video project!</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Etsy Video Generator</h1>
          <p className="text-gray-600 mt-2">Create stunning vertical product videos with Ken Burns effects</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex space-x-8">
            {['create', 'edit', 'history'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {activeTab === 'create' && <CreateProjectTab />}
        {activeTab === 'edit' && (currentProject ? <EditProjectTab /> : (
          <div className="text-center py-12">
            <p className="text-gray-500">No project selected. Create a new project or select from history.</p>
          </div>
        ))}
        {activeTab === 'history' && <HistoryTab />}
      </main>
    </div>
  );
};

export default VideoGenerator;