import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CourseCatalog from './CourseCatalog';
import CourseEvaluations from './CourseEvaluations';
import AppTutorial from './AppTutorial';
import config from './config';
import './App.css';
import { HelpCircle } from 'lucide-react';

// Add this function before the App component
const makeLinksClickable = (text) => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, (url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
};

function App() {
  const [activeTab, setActiveTab] = useState('catalog');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [advisors, setAdvisors] = useState([]);
  const [selectedAdvisor, setSelectedAdvisor] = useState('general');
  const [userMajor, setUserMajor] = useState(''); // Only keep major, remove academic level
  const [testMode, setTestMode] = useState(false); // Add test mode for cost-free testing
  const [error, setError] = useState('');
  const [showTutorial, setShowTutorial] = useState(false);
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    loadAdvisors();
    checkFirstVisit();
  }, []);

  const checkFirstVisit = () => {
    const hasVisited = localStorage.getItem('riceCatalog_hasVisited');
    if (!hasVisited) {
      setIsFirstVisit(true);
      setShowTutorial(true);
      localStorage.setItem('riceCatalog_hasVisited', 'true');
    }
  };

  const loadAdvisors = async () => {
    try {
      const response = await axios.get(`${config.BACKEND_URL}/api/advisors`);
      // Handle both object and array responses
      if (response.data.advisors) {
        if (Array.isArray(response.data.advisors)) {
          setAdvisors(response.data.advisors);
        } else {
          // Convert object to array format
          const advisorArray = Object.entries(response.data.advisors).map(([key, value]) => ({
            id: key,
            name: value
          }));
          setAdvisors(advisorArray);
        }
      }
    } catch (err) {
      console.error('Error loading advisors:', err);
      // Set default advisors if API fails
      setAdvisors([
        { id: 'general', name: '🎓 General Academic Advisor' },
        { id: 'computer_science', name: '💻 Computer Science Advisor' },
        { id: 'mathematics', name: '🔢 Mathematics Advisor' },
        { id: 'engineering', name: '🔧 Engineering Advisor' },
        { id: 'pre_med', name: '⚕️ Pre-Med Advisor' },
        { id: 'chemistry', name: '🧪 Chemistry Advisor' },
        { id: 'physics', name: '⚛️ Physics Advisor' }
      ]);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
      advisor: selectedAdvisor,
      major: userMajor
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError('');

    try {
      // Use new RAG flow endpoint
      const response = await axios.post(`${config.BACKEND_URL}/api/chat/message`, {
        message: inputMessage,
        advisor: selectedAdvisor,
        user_profile: userMajor ? { major: userMajor } : {},
        test_mode: testMode
      });

      const botMessage = {
        text: response.data.response, // New endpoint uses 'response' field
        sender: 'bot',
        timestamp: new Date().toISOString(),
        advisor: selectedAdvisor,
        metadata: response.data.metadata,
        search_results_count: response.data.search_results_count,
        response_time: response.data.response_time,
        model: response.data.model
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Error sending message:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError('');
  };

  const renderChatTab = () => (
    <div className="chat-container">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>🦉 O-Week Course Assistant</h2>
          <p>Your AI-powered academic advisor for freshmen</p>
        </div>

        <div className="quick-actions">
          <h3>Quick Actions</h3>
          <button 
            onClick={() => setInputMessage("What is COMP 140?")}
            className="quick-action-btn"
          >
            📚 About COMP 140
          </button>
          <button 
            onClick={() => setInputMessage("What courses should I take as a freshman?")}
            className="quick-action-btn"
          >
            📋 Freshman Courses
          </button>
          <button 
            onClick={() => setInputMessage("What are the prerequisites for COMP 182?")}
            className="quick-action-btn"
          >
            🔗 Prerequisites Help
          </button>
          <button 
            onClick={() => setInputMessage("What math courses do I need for computer science?")}
            className="quick-action-btn"
          >
            🔢 Math Requirements
          </button>
        </div>

        <div className="sidebar-footer">
          <button onClick={clearChat} className="clear-btn">
            🗑️ Clear Chat
          </button>
        </div>
      </div>

      <div className="main-content">
        <div className="chat-header">
          <h1>💬 Course Chat</h1>
          <p>Get personalized academic advice from your AI advisor</p>
          {testMode && (
            <div className="test-mode-indicator">
              🧪 Test Mode Active - No OpenAI Costs
            </div>
          )}
        </div>

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>Welcome to Rice Course Assistant! 🎓</h2>
              <p>I'm here to help you navigate your freshman year at Rice University. Ask me about:</p>
              <ul>
                <li>Specific courses like COMP 140, MATH 101, etc.</li>
                <li>Prerequisites and course sequences</li>
                <li>Freshman course recommendations</li>
                <li>Academic planning and scheduling</li>
              </ul>
              <div className="feature-highlight">
                <p><strong>💡 Pro Tip:</strong> Try asking "What is COMP 140?" to test our enhanced course search!</p>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message ${message.sender}`}>
                <div className="message-content">
                  <div className="message-text" dangerouslySetInnerHTML={{ __html: makeLinksClickable(message.text) }}></div>
                  {message.metadata?.related_link && (
                    <div className="message-link">
                      <a href={message.metadata.related_link.url} target="_blank" rel="noopener noreferrer">
                        {message.metadata.related_link.text}
                      </a>
                    </div>
                  )}

                  <div className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="message bot">
              <div className="message-content">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
                <small>
                  {testMode ? "Searching course database..." : "Generating response..."}
                </small>
              </div>
            </div>
          )}
        </div>

        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask your advisor anything about courses, requirements, or academic planning..."
            className="message-input"
            rows="3"
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'} Send
          </button>
        </div>
      </div>
    </div>
  );

    const renderResourcesTab = () => (
    <div className="resources-container">
      <div className="resources-header">
        <h2>🔗 Helpful Resources for Rice Students</h2>
        <p>Essential links and tools for your academic journey</p>
      </div>
      
      <div className="resources-grid">
        <a href="https://esther.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          🎯 ESTHER (Student Records)
        </a>
        <a href="https://courses.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          🎓 Rice Course Catalog
        </a>
        <a href="https://registrar.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          📋 Registrar's Office
        </a>
        <a href="https://oaa.rice.edu/" target="_blank" rel="noopener noreferrer" className="resource-link">
          👨‍🏫 Academic Advising
        </a>
        <a href="https://library.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          📖 Fondren Library
        </a>
        <a href="https://wellbeing.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          💚 Student Wellbeing
        </a>
        <a href="https://ccd.rice.edu/" target="_blank" rel="noopener noreferrer" className="resource-link">
          💼 Career Development
        </a>
        <a href="https://drc.rice.edu/" target="_blank" rel="noopener noreferrer" className="resource-link">
          ♿ Disability Resource Center
        </a>
        <a href="https://housing.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          🏠 Housing & Dining
        </a>
        <a href="https://studentactivities.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          🎉 Student Activities
        </a>
        <a href="https://recreation.rice.edu/" target="_blank" rel="noopener noreferrer" className="resource-link">
          🏃 Athletics & Recreation
        </a>
        <a href="https://transportation.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          🚌 Transportation
        </a>
        <a href="https://canvas.rice.edu" target="_blank" rel="noopener noreferrer" className="resource-link">
          📚 Canvas
        </a>
      </div>
    </div>
  );

  return (
    <div className="App">
      {/* Animated background elements */}
      <div className="app-blobs">
        {/* Morphing blob with animated path */}
        <svg className="blob morphing-blob" viewBox="0 0 200 200">
          <path fill="#002469" fillOpacity=".3">
            <animate attributeName="d" dur="12s" repeatCount="indefinite"
              values="M44.8,-67.6C56.7,-59.2,63.7,-44.2,68.2,-29.2C72.7,-14.2,74.7,0.8,70.2,14.2C65.7,27.6,54.7,39.4,41.7,48.2C28.7,57,14.3,62.8,-0.7,63.7C-15.7,64.6,-31.4,60.6,-44.2,52.1C-57,43.6,-66.8,30.6,-70.7,15.7C-74.6,0.8,-72.6,-15,-65.2,-28.2C-57.8,-41.4,-45,-52.9,-30.7,-60.7C-16.4,-68.5,-0.7,-72.6,14.2,-73.7C29.1,-74.8,58.2,-72.1,44.8,-67.6Z;
M54.8,-67.6C66.7,-59.2,73.7,-44.2,78.2,-29.2C82.7,-14.2,84.7,0.8,80.2,14.2C75.7,27.6,64.7,39.4,51.7,48.2C38.7,57,24.3,62.8,9.3,63.7C-5.7,64.6,-21.4,60.6,-34.2,52.1C-47,43.6,-56.8,30.6,-60.7,15.7C-64.6,0.8,-62.6,-15,-55.2,-28.2C-47.8,-41.4,-35,-52.9,-20.7,-60.7C-6.4,-68.5,9.3,-72.6,24.2,-73.7C39.1,-74.8,68.2,-72.1,54.8,-67.6Z;
M44.8,-67.6C56.7,-59.2,63.7,-44.2,68.2,-29.2C72.7,-14.2,74.7,0.8,70.2,14.2C65.7,27.6,54.7,39.4,41.7,48.2C28.7,57,14.3,62.8,-0.7,63.7C-15.7,64.6,-31.4,60.6,-44.2,52.1C-57,43.6,-66.8,30.6,-70.7,15.7C-74.6,0.8,-72.6,-15,-65.2,-28.2C-57.8,-41.4,-45,-52.9,-30.7,-60.7C-16.4,-68.5,-0.7,-72.6,14.2,-73.7C29.1,-74.8,58.2,-72.1,44.8,-67.6Z"
            />
          </path>
        </svg>
        {/* Additional blobs for color variety */}
        <svg className="blob blob1" viewBox="0 0 200 200"><path fill="#002469" fillOpacity=".4" d="M44.8,-67.6C56.7,-59.2,63.7,-44.2,68.2,-29.2C72.7,-14.2,74.7,0.8,70.2,14.2C65.7,27.6,54.7,39.4,41.7,48.2C28.7,57,14.3,62.8,-0.7,63.7C-15.7,64.6,-31.4,60.6,-44.2,52.1C-57,43.6,-66.8,30.6,-70.7,15.7C-74.6,0.8,-72.6,-15,-65.2,-28.2C-57.8,-41.4,-45,-52.9,-30.7,-60.7C-16.4,-68.5,-0.7,-72.6,14.2,-73.7C29.1,-74.8,58.2,-72.1,44.8,-67.6Z" transform="translate(100 100)"/></svg>
        <svg className="blob blob2" viewBox="0 0 200 200"><path fill="#5E6062" fillOpacity=".3" d="M38.7,-62.2C51.2,-54.2,62.2,-43.2,67.2,-29.8C72.2,-16.4,71.2,-0.6,66.2,13.2C61.2,27,52.2,38.8,40.2,47.2C28.2,55.6,14.1,60.6,-0.7,61.4C-15.5,62.2,-31,58.8,-43.2,50.2C-55.4,41.6,-64.2,27.8,-67.2,13.2C-70.2,-1.4,-67.4,-16.8,-59.2,-29.2C-51,-41.6,-37.4,-51,-22.2,-57.2C-7,-63.4,9.8,-66.2,25.2,-63.2C40.6,-60.2,54.2,-51.2,38.7,-62.2Z" transform="translate(100 100)"/></svg>
        <svg className="blob blob3" viewBox="0 0 200 200"><path fill="#ffffff" fillOpacity=".2" d="M44.8,-67.6C56.7,-59.2,63.7,-44.2,68.2,-29.2C72.7,-14.2,74.7,0.8,70.2,14.2C65.7,27.6,54.7,39.4,41.7,48.2C28.7,57,14.3,62.8,-0.7,63.7C-15.7,64.6,-31.4,60.6,-44.2,52.1C-57,43.6,-66.8,30.6,-70.7,15.7C-74.6,0.8,-72.6,-15,-65.2,-28.2C-57.8,-41.4,-45,-52.9,-30.7,-60.7C-16.4,-68.5,-0.7,-72.6,14.2,-73.7C29.1,-74.8,58.2,-72.1,44.8,-67.6Z" transform="translate(100 100)"/></svg>
      </div>
      
      {/* Animated floating dots */}
      <div className="app-dots">
        {Array.from({length: 15}).map((_, i) => (
          <span key={i} className={`dot dot${i+1}`}></span>
        ))}
      </div>

      <nav className="main-nav">
        <div className="nav-brand">
          <h1>🍌 O-Week Course Assistant</h1>
        </div>
        <div className="nav-tabs">
          {/* Move help button here, before Course Catalog */}
          <button
            type="button"
            className="help-fab"
            onClick={() => setShowTutorial(true)}
            title="Show Tutorial"
          >
            <HelpCircle className="help-fab-icon" />
          </button>
          <button 
            className={`nav-tab ${activeTab === 'catalog' ? 'active' : ''}`}
            onClick={() => setActiveTab('catalog')}
          >
            🔍 Course Catalog
          </button>
          <button 
            className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            data-tab="chat"
          >
            💬 Course Chat
          </button>
          <button 
            className={`nav-tab ${activeTab === 'evaluations' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluations')}
          >
            📊 Course Evaluations
          </button>
          <button 
            className={`nav-tab ${activeTab === 'resources' ? 'active' : ''}`}
            onClick={() => setActiveTab('resources')}
          >
            🔗 Helpful Resources
          </button>
        </div>
      </nav>

      <main className="main-content">
        {activeTab === 'chat' && renderChatTab()}
        {activeTab === 'catalog' && <CourseCatalog onNavigateToTab={setActiveTab} />}
        {activeTab === 'evaluations' && <CourseEvaluations />}
        {activeTab === 'resources' && renderResourcesTab()}
      </main>

      {/* Tutorial Component */}
      <AppTutorial
        isOpen={showTutorial}
        onClose={() => setShowTutorial(false)}
        onComplete={() => {
          setShowTutorial(false);
        }}
        onNavigateToTab={(tab) => setActiveTab(tab)}
      />

      {/* Footer */}
      <footer className="main-footer">
        <div className="footer-content">
          <p>Made with ❤️ by Rice Students 🍌</p>
        </div>
      </footer>
    </div>
  );
}

export default App; 