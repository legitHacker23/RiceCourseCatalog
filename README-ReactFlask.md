# 🦉 Rice Course Assistant - React + Flask

A modern web application for Rice University course planning and academic advising, powered by GPT-4.1 Nano.

## 🏗️ Architecture

- **Backend**: Flask API with GPT-4.1 Nano integration
- **Frontend**: React with modern UI/UX
- **AI Model**: GPT-4.1 Nano (faster, cheaper, larger context)

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements-flask.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run Flask backend
cd backend
python app.py
```

The backend will run on `http://localhost:5000`

### 2. Frontend Setup

```bash
# Install Node.js dependencies
cd frontend
npm install

# Start React development server
npm start
```

The frontend will run on `http://localhost:3000`

## 📁 Project Structure

```
RiceCatalog/
├── backend/
│   └── app.py              # Flask API server
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── App.css         # Rice-themed styling
│   │   ├── index.js        # React entry point
│   │   └── index.css       # Global styles
│   ├── public/
│   │   └── index.html      # HTML template
│   └── package.json        # React dependencies
├── data/                   # Course data (from original)
├── requirements-flask.txt  # Backend dependencies
└── README-ReactFlask.md    # This file
```

## 🔧 API Endpoints

### Backend (Flask)

- `GET /api/health` - Health check
- `GET /api/advisors` - Get available advisors
- `POST /api/ask` - Ask a question to the assistant
- `GET /api/courses` - Get course data
- `GET /api/departments` - Get department list

### Example API Usage

```javascript
// Ask a question
const response = await fetch('/api/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: "What are the CS major requirements?",
    advisor: "computer_science"
  })
});
```

## 🎯 Features

### ✅ Converted from Streamlit
- **Chat Interface**: Natural language course planning
- **Advisor Selection**: 14 specialized academic advisors
- **GPT-4.1 Nano**: Faster, cheaper, larger context window
- **Rice Theming**: Official Rice University colors and branding

### 🚀 New React Features
- **Responsive Design**: Works on desktop and mobile
- **Real-time Chat**: Instant responses with loading states
- **Quick Actions**: Pre-built common questions
- **Clean UI**: Modern, professional interface

## 🎨 Design

### Rice University Theme
- **Colors**: Rice Blue (#002469) and Rice Gray (#5E6062)
- **Fonts**: Playfair Display (headers) and Lato (body)
- **Owl Mascot**: Animated floating owl icon
- **Responsive**: Mobile-first design

## 💰 Cost Savings

By using GPT-4.1 Nano instead of GPT-4o:
- **33% cheaper** input tokens ($0.10 vs $0.15)
- **33% cheaper** output tokens ($0.40 vs $0.60)
- **8x larger** context window (1M vs 128K tokens)
- **Faster** response times

## 🔄 Migration from Streamlit

This React-Flask app directly converts your existing `rice_course_assistant.py`:

### What's the Same:
- All advisor prompts and logic
- GPT integration and course data processing
- Core functionality and features

### What's Better:
- Modern web technology stack
- Better performance and scalability
- Professional UI/UX
- Mobile responsiveness
- API-first architecture

## 🚀 Deployment

### Development
```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Frontend
cd frontend && npm start
```

### Production
```bash
# Build React app
cd frontend && npm run build

# Serve with Flask (or use nginx/apache)
# Configure Flask to serve static files from frontend/build
```

## 🔧 Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 📊 Performance

- **Response Time**: ~1-3 seconds (GPT-4.1 Nano)
- **Context Window**: 1M tokens (8x larger than GPT-4o Mini)
- **Cost**: 33% cheaper than GPT-4o Mini
- **Scalability**: API-first architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both backend and frontend
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**🦉 "Unconventional Wisdom" - Rice University, Est. 1912** 