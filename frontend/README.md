# PS Knowledge Copilot - React Frontend

Modern React + Vite frontend for the PS Knowledge Copilot.

## Quick Start

### Prerequisites
- Node.js 18+ 
- FastAPI backend running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

### Running with Backend

1. **Start the FastAPI backend** (in project root):
```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# Start API server
uvicorn app.api.main:app --reload --port 8000
```

2. **Start the React frontend** (in `frontend/` directory):
```bash
npm run dev
```

## Features

- **Modern UI**: Clean, responsive design
- **Real-time Queries**: Instant search with context-aware answers
- **Source Citations**: Shows chunked document sources
- **Quick Actions**: Pre-built example queries
- **Health Monitoring**: Live API status indicator

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx  # Query input form
│   │   ├── SourceCards.jsx    # Source document display
│   │   └── Sidebar.jsx        # Admin tools panel
│   ├── hooks/
│   │   └── useRAG.js          # RAG query state management
│   ├── api/
│   │   └── ragService.js      # API client
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # Entry point
│   └── index.css              # Design system
├── package.json
├── vite.config.js             # Vite config with API proxy
└── index.html
```

## Production Build

```bash
npm run build
```

Output will be in `dist/` directory.
