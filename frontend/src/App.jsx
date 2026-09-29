import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Ticket,
  Copy,
  Check,
  Plus,
  MessageSquare,
  Users,
  ShoppingCart,
  AlertTriangle,
  FileText,
  Settings,
  Menu,
  X,
  Loader2
} from 'lucide-react';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const STARTER_PROMPTS = [
  { prompt: 'Find Manoj Kumar' },
  { prompt: 'Show C001 orders' },
  { prompt: 'Find pending complaints' },
  { prompt: 'Search company policy' },
];

const NAV_ITEMS = [
  { label: 'New Chat', icon: Plus, action: 'new-chat' },
  { label: 'Customers', icon: Users, action: 'customers' },
  { label: 'Orders', icon: ShoppingCart, action: 'orders' },
  { label: 'Complaints', icon: AlertTriangle, action: 'complaints' },
  { label: 'Policies', icon: FileText, action: 'policies' },
  { label: 'Settings', icon: Settings, action: 'settings' },
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [copiedId, setCopiedId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeNav, setActiveNav] = useState('new-chat');

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const checkHealth = async () => {
    setBackendStatus('checking');
    try {
      const res = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        setBackendStatus('online');
        setErrorMessage(null);
      } else {
        setBackendStatus('offline');
      }
    } catch {
      try {
        const fallbackRes = await fetch('/health');
        if (fallbackRes.ok) {
          setBackendStatus('online');
          setErrorMessage(null);
          return;
        }
      } catch {
        // ignore
      }
      setBackendStatus('offline');
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleInputChange = (e) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const sendMessage = async (overrideText) => {
    const textToSend = (overrideText !== undefined ? overrideText : input).trim();
    if (!textToSend || loading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setErrorMessage(null);
    setLoading(true);
    setLoadingStep('Processing...');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      setLoadingStep('Querying assistant...');

      let response;
      try {
        response = await fetch(`${API_BASE_URL}/api/assistant`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ message: textToSend })
        });
      } catch (err) {
        response = await fetch('/api/assistant', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ message: textToSend })
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: HTTP ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: data.response || 'No response returned from the assistant.',
        decision: data.decision || 'NO_ACTION',
        ticket: data.ticket || '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setBackendStatus('online');
    } catch (err) {
      console.error('API Error:', err);
      setErrorMessage(err.message || 'Failed to connect to the assistant.');
      setBackendStatus('offline');
    } finally {
      setLoading(false);
      setLoadingStep('');
    }
  };

  const clearChat = () => {
    setMessages([]);
    setErrorMessage(null);
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleNavClick = (action) => {
    setActiveNav(action);
    setSidebarOpen(false);
    if (action === 'new-chat') {
      clearChat();
    } else if (action === 'customers') {
      sendMessage('Show all customers');
    } else if (action === 'orders') {
      sendMessage('Show all orders');
    } else if (action === 'complaints') {
      sendMessage('Show all complaints');
    } else if (action === 'policies') {
      sendMessage('Search company policy');
    }
  };

  const renderDecisionBadge = (decision) => {
    if (!decision) return null;
    switch (decision) {
      case 'CREATE_TICKET':
        return (
          <span className="decision-badge create-ticket">
            <CheckCircle2 size={12} />
            Ticket Created
          </span>
        );
      case 'MORE_INFORMATION_REQUIRED':
        return (
          <span className="decision-badge more-info">
            <AlertCircle size={12} />
            More Info Required
          </span>
        );
      case 'NO_ACTION':
      default:
        return (
          <span className="decision-badge no-action">
            <Check size={12} />
            Complete
          </span>
        );
    }
  };

  const showWelcome = messages.length === 0;

  return (
    <div className="app-layout">
      {/* Sidebar Overlay (mobile) */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`} id="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="sidebar-logo">
              <Bot size={16} />
            </div>
            <span className="sidebar-brand-text">DCI AI Business Assistant</span>
          </div>
          <button
            className="new-chat-btn"
            onClick={() => handleNavClick('new-chat')}
            id="new-chat-button"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.filter(item => item.action !== 'new-chat').map((item) => (
            <button
              key={item.action}
              className={`nav-item ${activeNav === item.action ? 'active' : ''}`}
              onClick={() => handleNavClick(item.action)}
              id={`nav-${item.action}`}
            >
              <item.icon size={16} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          Powered by LangGraph + Ollama
        </div>
      </aside>

      {/* Main Area */}
      <div className="main-area">
        {/* Header */}
        <header className="header" id="app-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="mobile-menu-btn"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title="Toggle menu"
            >
              {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
            <span className="header-title">DCI AI Business Assistant</span>
          </div>

          <div className="header-right">
            <div
              id="status-indicator"
              className={`status-indicator ${backendStatus === 'offline' ? 'offline' : ''}`}
              title={backendStatus === 'online' ? 'Backend Connected' : 'Backend Offline'}
            >
              <span className="status-dot" />
              <span>
                {backendStatus === 'online' ? 'Connected' : backendStatus === 'checking' ? 'Connecting...' : 'Offline'}
              </span>
            </div>

            <button
              className="header-icon-btn"
              onClick={checkHealth}
              title="Refresh Status"
              id="check-health-button"
            >
              <RefreshCw size={15} className={backendStatus === 'checking' ? 'spin' : ''} />
            </button>
          </div>
        </header>

        {/* Error Banner */}
        {errorMessage && (
          <div className="error-banner" id="error-banner">
            <div className="error-content">
              <AlertCircle size={16} />
              <span><strong>Error:</strong> {errorMessage}</span>
            </div>
            <button
              className="error-retry-btn"
              onClick={() => {
                checkHealth();
                const lastUser = [...messages].reverse().find(m => m.role === 'user');
                if (lastUser) sendMessage(lastUser.content);
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Chat Area */}
        <main className="chat-container" id="chat-container">
          <div className="chat-scroll-inner">
            {/* Welcome Screen */}
            {showWelcome && (
              <div className="welcome-container" id="welcome-screen">
                <div className="welcome-logo">
                  <Bot size={22} />
                </div>
                <h1 className="welcome-title">DCI AI Business Assistant</h1>
                <p className="welcome-subtitle">How can I help you today?</p>

                <div className="prompt-chips">
                  {STARTER_PROMPTS.map((item, index) => (
                    <button
                      key={index}
                      id={`prompt-chip-${index}`}
                      className="prompt-chip"
                      onClick={() => sendMessage(item.prompt)}
                      disabled={loading}
                    >
                      {item.prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.role}`} id={`message-${msg.id}`}>
                <div className="message-content">
                  {msg.role === 'assistant' && msg.decision && renderDecisionBadge(msg.decision)}

                  <div className="message-text">
                    {msg.content}
                  </div>

                  {msg.ticket && (
                    <div className="ticket-card" id={`ticket-card-${msg.id}`}>
                      <div className="ticket-header">
                        <span className="ticket-title">
                          <Ticket size={14} />
                          Support Ticket Created
                        </span>
                        <span className="ticket-status-pill">Generated</span>
                      </div>
                      <pre className="ticket-content">{msg.ticket}</pre>
                    </div>
                  )}

                  <div className="message-meta">
                    <span className="message-time">{msg.timestamp}</span>
                    {msg.role === 'assistant' && (
                      <button
                        className="copy-btn"
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        title="Copy response"
                      >
                        {copiedId === msg.id ? <Check size={11} /> : <Copy size={11} />}
                        {copiedId === msg.id ? 'Copied' : 'Copy'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading */}
            {loading && (
              <div className="loading-row" id="loading-row">
                <div className="loading-bubble">
                  <div className="loading-status-text">
                    <Loader2 size={14} className="spin" />
                    <span>{loadingStep || 'Processing...'}</span>
                  </div>
                  <div className="dots-wrapper">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Input Section */}
        <footer className="input-section" id="input-section">
          <div className="input-wrapper">
            <form
              className="input-form"
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage();
              }}
            >
              <textarea
                id="message-input"
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about customers, orders, complaints or company policies..."
                className="chat-input"
                disabled={loading}
              />

              <button
                type="submit"
                id="send-button"
                className="send-btn"
                disabled={loading || !input.trim()}
                title="Send message"
              >
                {loading ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
              </button>
            </form>

            <div className="input-footer">
              <span>Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for new line</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
