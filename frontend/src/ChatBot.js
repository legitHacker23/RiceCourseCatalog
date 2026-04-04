import React, { useState, useEffect, useRef, useCallback } from 'react';
import config from './config';
import './ChatBot.css';

const ChatBot = ({ selectedAdvisor = 'general', userProfile = {} }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [searchProgress, setSearchProgress] = useState(null);
  const [contextInfo, setContextInfo] = useState(null);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Initialize chat system (REST API mode)
  const initializeChat = useCallback(() => {
    console.log('Chat system initialized (REST API mode)');
    setIsConnected(true); // Mark as connected for UI purposes
    
    // Add welcome message
    addMessage({
      type: 'system',
      content: '🦉 Rice Course Assistant connected! How can I help you today?',
      timestamp: Date.now()
    });
  }, []);

  // WebSocket message handler (not used in REST API mode)
  // Kept for potential future WebSocket implementation
  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message received:', data);
  };

  // Add message to chat history
  const addMessage = (message) => {
    setMessages(prev => [...prev, { id: Date.now(), ...message }]);
  };

  // Send message via REST API
  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = inputMessage.trim();
    
    // Add user message to UI immediately
    addMessage({
      type: 'user',
      content: userMessage,
      timestamp: Date.now()
    });
    
    // Clear input immediately
    setInputMessage('');
    
    // Add typing indicator
    const typingId = Date.now();
    addMessage({
      id: typingId,
      type: 'system',
      content: '🤖 Thinking...',
      timestamp: Date.now()
    });
    
    try {
      // Send message to REST API
      const response = await fetch(`${config.BACKEND_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          advisor: selectedAdvisor,
          user_profile: {
            major: 'Computer Science', // You can make this dynamic later
            completed_courses: [],
            current_year: 'Junior'
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Remove typing indicator
      setMessages(prev => prev.filter(msg => msg.id !== typingId));
      
      // Add bot response
      addMessage({
        type: 'bot',
        content: data.response || data.message || 'Sorry, I encountered an error.',
        timestamp: Date.now(),
        metadata: data.metadata || {}
      });
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Remove typing indicator
      setMessages(prev => prev.filter(msg => msg.id !== typingId));
      
      // Add error message
      addMessage({
        type: 'system',
        content: 'Sorry, I encountered an error. Please try again or check that the backend server is running.',
        timestamp: Date.now()
      });
    }
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Effects
  useEffect(() => {
    initializeChat();
  }, [initializeChat]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamingMessage]);

  // User profile updates are handled in REST API requests
  // No need for real-time profile updates since we're using REST API

  return (
    <div className="chat-bot-container">
      {/* Connection Status */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className="status-indicator"></span>
        {isConnected ? 'Connected to Rice Assistant' : 'Connecting...'}
      </div>

      {/* Chat Messages */}
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              {message.content}
              {message.metadata && (
                <div className="message-metadata">
                  <small>
                    {message.metadata.documents_count && 
                      `📚 ${message.metadata.documents_count} sources • `
                    }
                    Advisor: {message.metadata.advisor || selectedAdvisor}
                  </small>
                </div>
              )}
            </div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {/* Live Streaming Message */}
        {currentStreamingMessage && (
          <div className="message assistant streaming">
            <div className="message-content">
              {currentStreamingMessage}
              <span className="streaming-cursor">|</span>
            </div>
          </div>
        )}
        
        {/* Progress Indicators */}
        {isTyping && (
          <div className="typing-indicators">
            {searchProgress && (
              <div className="search-progress">
                🔍 Found {searchProgress.found_documents} relevant courses...
              </div>
            )}
            {contextInfo && (
              <div className="context-info">
                📖 Analyzing {contextInfo.documents_count} sources ({contextInfo.context_length} words)...
              </div>
            )}
            {!searchProgress && !contextInfo && (
              <div className="typing-indicator">
                <span>🤔 Thinking</span>
                <div className="dots">
                  <span>.</span>
                  <span>.</span>
                  <span>.</span>
                </div>
              </div>
            )}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? 
              "Ask about Rice courses, requirements, or academic planning..." : 
              "Connecting to assistant..."
            }
            disabled={!isConnected || isTyping}
            rows="2"
          />
          <button 
            onClick={sendMessage}
            disabled={!isConnected || !inputMessage.trim() || isTyping}
            className="send-button"
          >
            Send
          </button>
        </div>
        
        {/* Quick Actions */}
        <div className="quick-actions">
          <button onClick={() => setInputMessage("What courses should I take next semester?")}>
            📚 Course Recommendations
          </button>
          <button onClick={() => setInputMessage("What are the prerequisites for computer science courses?")}>
            📋 Prerequisites
          </button>
          <button onClick={() => setInputMessage("Show me Fall 2025 courses in my major")}>
            🗓️ Fall 2025 Courses
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;
