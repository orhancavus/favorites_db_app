import React, { useState, useEffect, useRef } from 'react';
import './index.css';

function App() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('gemma3');
  const [host, setHost] = useState('http://localhost:11434');
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed, error
  const [progress, setProgress] = useState({ processed: 0, total: 0, current: '' });
  const ws = useRef(null);

  useEffect(() => {
    // Connect to WebSocket for progress updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/progress`;

    const connect = () => {
      ws.current = new WebSocket(wsUrl);

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'start') {
          setStatus('processing');
          setProgress({ processed: 0, total: data.total, current: 'Starting...' });
        } else if (data.type === 'progress') {
          setProgress({
            processed: data.processed,
            total: data.total,
            current: data.current
          });
        } else if (data.type === 'complete') {
          setStatus('completed');
        } else if (data.type === 'error') {
          setStatus('error');
          alert(data.message);
        }
      };

      ws.current.onclose = () => {
        setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);
    formData.append('host', host);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const result = await response.json();
      console.log('Upload success:', result);
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  const progressPercentage = progress.total > 0
    ? Math.round((progress.processed / progress.total) * 100)
    : 0;

  return (
    <div className="glass-card">
      <h1>Bookmark Processor</h1>
      <p className="subtitle">Upload your Safari bookmarks to analyze and categorize them with AI.</p>

      <div className="upload-section">
        <div className="config-grid">
          <div className="input-group">
            <label>Ollama Model</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. gemma3"
            />
          </div>
          <div className="input-group">
            <label>Ollama Host</label>
            <input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="http://localhost:11434"
            />
          </div>
        </div>

        <div
          className="drop-zone"
          onClick={() => document.getElementById('fileInput').click()}
        >
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p>{file ? file.name : "Click to select or drag & drop bookmarks.html"}</p>
          <input
            id="fileInput"
            type="file"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            accept=".html"
          />
        </div>

        <button
          className="upload-button"
          onClick={handleUpload}
          disabled={!file || status === 'uploading' || status === 'processing'}
        >
          {status === 'processing' ? 'Processing...' : 'Start Analysis'}
        </button>
      </div>

      {(status === 'processing' || status === 'completed') && (
        <div className="progress-container">
          <div className="status-info">
            <span>{status === 'completed' ? 'Finished' : 'Processing Bookmarks...'}</span>
            <span>{progress.processed} / {progress.total} ({progressPercentage}%)</span>
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
          {status === 'processing' && (
            <div className="current-item processing">
              Current: {progress.current}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
