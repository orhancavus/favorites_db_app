import React, { useState, useEffect, useRef } from 'react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'dashboard'
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('gemma3');
  const [host, setHost] = useState('http://localhost:11434');
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState({ processed: 0, total: 0, current: '' });

  // Dashboard states
  const [bookmarks, setBookmarks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  const ws = useRef(null);

  useEffect(() => {
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
          setProgress({ processed: data.processed, total: data.total, current: data.current });
        } else if (data.type === 'complete') {
          setStatus('completed');
          // Refresh dashboard data if it was open
          if (activeTab === 'dashboard') fetchDashboardData();
        } else if (data.type === 'error') {
          setStatus('error');
          alert(data.message);
        }
      };
      ws.current.onclose = () => setTimeout(connect, 3000);
    };
    connect();
    return () => { if (ws.current) ws.current.close(); };
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboardData();
    }
  }, [activeTab, searchQuery]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [bRes, cRes] = await Promise.all([
        fetch(`http://localhost:8000/bookmarks?q=${encodeURIComponent(searchQuery)}`),
        fetch('http://localhost:8000/categories')
      ]);
      const bData = await bRes.json();
      const cData = await cRes.json();
      setBookmarks(bData);
      setCategories(cData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCardClick = (e, bookmark) => {
    // If clicking a link directly, don't trigger the card expansion
    if (e.target.tagName === 'A') return;

    // Toggle expansion
    setExpandedId(expandedId === bookmark.id ? null : bookmark.id);
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);
    formData.append('host', host);
    try {
      const response = await fetch('http://localhost:8000/upload', { method: 'POST', body: formData });
      if (!response.ok) throw new Error('Upload failed');
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  const filteredBookmarks = selectedCategory === 'All'
    ? bookmarks
    : bookmarks.filter(b => b.category === selectedCategory);

  return (
    <div className="glass-card">
      <div className="card-header-main">
        <h1>Bookmark Processor</h1>
        <p className="subtitle">AI-powered organization for your digital library.</p>
      </div>

      <div className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload
        </button>
        <button
          className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
      </div>

      {activeTab === 'upload' ? (
        <div className="upload-section">
          <div className="config-grid">
            <div className="input-group">
              <label>Ollama Model</label>
              <input type="text" value={model} onChange={(e) => setModel(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Ollama Host</label>
              <input type="text" value={host} onChange={(e) => setHost(e.target.value)} />
            </div>
          </div>
          <div className="drop-zone" onClick={() => document.getElementById('fileInput').click()}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
            <p>{file ? file.name : "Select bookmarks.html"}</p>
            <input id="fileInput" type="file" style={{ display: 'none' }} onChange={(e) => setFile(e.target.files[0])} accept=".html" />
          </div>
          <button className="upload-button" onClick={handleUpload} disabled={!file || status === 'processing'}>
            {status === 'processing' ? 'Processing...' : 'Start Analysis'}
          </button>
          {(status === 'processing' || status === 'completed') && (
            <div className="progress-container">
              <div className="status-info">
                <span>{status === 'completed' ? 'Finished' : 'Processing...'}</span>
                <span>{progress.processed} / {progress.total}</span>
              </div>
              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: `${progress.total > 0 ? (progress.processed / progress.total) * 100 : 0}%` }}></div></div>
              {status === 'processing' && <div className="current-item processing">Current: {progress.current}</div>}
            </div>
          )}
        </div>
      ) : (
        <div className="dashboard-section">
          <div className="dashboard-controls">
            <div className="search-bar">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="Search by title, summary or category..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="category-summary">
              <button
                className={`category-pill ${selectedCategory === 'All' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('All')}
              >
                All <span className="category-count">{bookmarks.length}</span>
              </button>
              {categories.map(cat => (
                <button
                  key={cat.name}
                  className={`category-pill ${selectedCategory === cat.name ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(cat.name)}
                >
                  {cat.name} <span className="category-count">{cat.count}</span>
                </button>
              ))}
            </div>
          </div>

          {isLoading ? (
            <div className="loading-state">Loading bookmarks...</div>
          ) : (
            <div className="bookmark-grid">
              {filteredBookmarks.length > 0 ? filteredBookmarks.map(bookmark => (
                <div
                  key={bookmark.id}
                  className="bookmark-card"
                  onClick={(e) => handleCardClick(e, bookmark)}
                >
                  <div className="card-header">
                    <a
                      href={bookmark.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="card-title"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {bookmark.title || 'Untitled'}
                    </a>
                    <span className="card-category">{bookmark.category}</span>
                  </div>
                  <p className={`card-summary ${expandedId === bookmark.id ? 'expanded' : ''}`}>
                    {bookmark.summary}
                  </p>
                  <div className="card-footer">
                    <span>{new URL(bookmark.url).hostname}</span>
                    <span>{new Date(bookmark.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              )) : (
                <div className="no-results">No bookmarks found.</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
