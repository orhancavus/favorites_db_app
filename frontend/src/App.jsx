import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'dashboard'
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('gemma3');
  const [host, setHost] = useState('http://localhost:11434');
  const [provider, setProvider] = useState('ollama'); // 'ollama' or 'gemini'
  const [geminiKey, setGeminiKey] = useState('');
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState({ processed: 0, total: 0, current: '' });
  const [results, setResults] = useState({ added: 0, skipped: 0, total: 0, tokens: 0 });

  // Dashboard states
  const [bookmarks, setBookmarks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [summaryData, setSummaryData] = useState([]);
  const [chartMinCount, setChartMinCount] = useState(10);
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
          setResults({ added: data.added, skipped: data.skipped, total: data.total, tokens: data.tokens });
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
  }, [activeTab, searchQuery, chartMinCount]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [bRes, cRes, sRes] = await Promise.all([
        fetch(`http://localhost:8000/bookmarks?q=${encodeURIComponent(searchQuery)}`),
        fetch('http://localhost:8000/categories'),
        fetch(`http://localhost:8000/category-summary?min_count=${chartMinCount}`)
      ]);
      const bData = await bRes.json();
      const cData = await cRes.json();
      const sData = await sRes.json();

      setBookmarks(bData);
      setCategories(cData);
      setSummaryData(Array.isArray(sData) ? sData : []);
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

  const handleTitleClick = (e, url) => {
    e.preventDefault();
    e.stopPropagation();
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    setResults({ added: 0, skipped: 0, total: 0, tokens: 0 });
    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', provider);
    formData.append('model', model);
    formData.append('host', host);
    if (geminiKey) formData.append('gemini_api_key', geminiKey);
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
              <label>LLM Provider</label>
              <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                <option value="ollama">Local (Ollama)</option>
                <option value="gemini">Cloud (Google Gemini)</option>
              </select>
            </div>
            {provider === 'ollama' ? (
              <>
                <div className="input-group">
                  <label>Ollama Model</label>
                  <input type="text" value={model} onChange={(e) => setModel(e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Ollama Host</label>
                  <input type="text" value={host} onChange={(e) => setHost(e.target.value)} />
                </div>
              </>
            ) : (
              <div className="input-group full-width">
                <label>Gemini API Key</label>
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="Paste your Gemini API key here (or leave blank to use server-side env)"
                />
              </div>
            )}
          </div>
          <div
            className="drop-zone"
            onClick={() => document.getElementById('fileInput').click()}
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                setFile(e.dataTransfer.files[0]);
              }
            }}
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
            <p>{file ? file.name : "Select bookmarks.html (Safari, Edge, Chrome)"}</p>
            <input id="fileInput" type="file" style={{ display: 'none' }} onChange={(e) => setFile(e.target.files[0])} accept=".html" />
          </div>
          <button className="upload-button" onClick={handleUpload} disabled={!file || status === 'processing'}>
            {status === 'processing' ? 'Processing...' : 'Start Analysis'}
          </button>
          {status === 'processing' && (
            <div className="progress-container">
              <div className="status-info">
                <span>Processing...</span>
                <span>{progress.processed} / {progress.total}</span>
              </div>
              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: `${progress.total > 0 ? (progress.processed / progress.total) * 100 : 0}%` }}></div></div>
              <div className="current-item processing">Current: {progress.current}</div>
            </div>
          )}
          {status === 'completed' && (
            <div className="progress-container">
              <div className="status-info" style={{ justifyContent: 'center', textAlign: 'center' }}>
                <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '1rem', width: '100%' }}>
                  <h3 style={{ color: 'var(--success)', marginBottom: '0.5rem' }}>Analysis Complete!</h3>
                  <div style={{ display: 'flex', justifyContent: 'space-around', gap: '1rem' }}>
                    <div><strong>{results.added}</strong> <span style={{ color: 'var(--text-muted)' }}>Newly Added</span></div>
                    <div><strong>{results.skipped}</strong> <span style={{ color: 'var(--text-muted)' }}>Skipped</span></div>
                    <div><strong>{results.tokens.toLocaleString()}</strong> <span style={{ color: 'var(--text-muted)' }}>Tokens</span></div>
                    <div><strong>{results.total}</strong> <span style={{ color: 'var(--text-muted)' }}>Total</span></div>
                  </div>
                </div>
              </div>
              <button className="upload-button" onClick={() => setStatus('idle')} style={{ marginTop: '1rem', background: 'rgba(255, 255, 255, 0.1)' }}>
                Process Another File
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="dashboard-section">
          {summaryData.length > 0 && (
            <div className="chart-container glass-panel">
              <div className="chart-controls">
                <h3 className="chart-title">Category Distribution</h3>
                <div className="chart-config-item">
                  <label htmlFor="minCount">Min Bookmarks</label>
                  <input
                    id="minCount"
                    type="number"
                    value={chartMinCount}
                    onChange={(e) => setChartMinCount(Math.max(1, parseInt(e.target.value) || 1))}
                    className="min-count-input"
                  />
                </div>
              </div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={summaryData}
                    margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="category"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
                      interval={0}
                      angle={-45}
                      textAnchor="end"
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
                    />
                    <Tooltip
                      cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                      contentStyle={{
                        backgroundColor: '#1a1a1a',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                    />
                    <Bar dataKey="count" fill="#10B981" radius={[4, 4, 0, 0]}>
                      {summaryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill="#10B981" fillOpacity={0.8 + (index % 2) * 0.2} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

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
              <button
                className="category-pill export-pill"
                onClick={() => window.location.href = 'http://localhost:8000/export'}
                title="Download categorized bookmarks as HTML"
              >
                📥 Export All
              </button>
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
                      className="card-title"
                      onClick={(e) => handleTitleClick(e, bookmark.url)}
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
