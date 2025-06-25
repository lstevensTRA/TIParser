# TI Parser - Backend & Frontend Setup

## Current Status

✅ **Backend is running and fully functional** on port 3001
❌ **Frontend Vite has compatibility issues** with current Node.js version

## Working Setup

### Backend (Node.js/Express)
- **Port**: 3001
- **Status**: ✅ Running and fully functional
- **Health Check**: http://localhost:3001/api/health
- **Features**: Authentication, WI Parser, API endpoints

### Frontend Options

Since the Vite frontend has Node.js compatibility issues, I've created two working alternatives:

#### Option 1: Simple HTML Test Page
- **File**: `test-frontend.html`
- **Access**: http://localhost:8080/test-frontend.html
- **Features**: Basic API testing, file upload, health checks

#### Option 2: React App (CDN-based)
- **File**: `simple-react-app.html`
- **Access**: http://localhost:8080/simple-react-app.html
- **Features**: Full React app with tabs, file parsing, authentication

## How to Start Everything

### 1. Start Backend
```bash
cd backend
npm run dev
```
The backend will start on port 3001.

### 2. Start Test Server
```bash
python3 -m http.server 8080
```
This serves the HTML test files.

### 3. Access the Applications

#### Backend API
- **Health Check**: http://localhost:3001/api/health
- **API Base**: http://localhost:3001/api

#### Frontend Test Pages
- **Simple Test**: http://localhost:8080/test-frontend.html
- **React App**: http://localhost:8080/simple-react-app.html

## API Endpoints

### Health Check
- `GET /api/health` - Backend status

### Authentication
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/test` - Test connection
- `POST /api/auth/refresh` - Refresh authentication

### Parsers
- `POST /api/parse/wi` - Parse WI documents
- `POST /api/parse/at` - Parse AT documents
- `POST /api/parse/roa` - Parse ROA documents
- `POST /api/parse/trt` - Parse TRT documents

### Analysis
- `POST /api/analysis/comprehensive` - Comprehensive analysis
- `POST /api/analysis/compare` - Compare documents
- `GET /api/analysis/tax-summary` - Get tax summary
- `POST /api/analysis/recommendations` - Get recommendations

### Clients
- `GET /api/clients` - Get all clients
- `POST /api/clients` - Create new client
- `GET /api/clients/:id` - Get specific client
- `PUT /api/clients/:id` - Update client
- `DELETE /api/clients/:id` - Delete client

### TPS Integration
- `GET /api/tps/status` - TPS connection status
- `POST /api/tps/sync` - Sync with TPS
- `GET /api/tps/data` - Get TPS data

## Testing the Setup

### 1. Test Backend Health
```bash
curl http://localhost:3001/api/health
```
Should return: `{"status":"OK","timestamp":"...","version":"1.0.0"}`

### 2. Test File Upload
1. Open http://localhost:8080/simple-react-app.html
2. Go to "Parsers" tab
3. Select a PDF file
4. Choose parser type (WI, AT, ROA, TRT)
5. Click "Parse Document"

### 3. Test Authentication
1. Open the React app
2. Go to "Authentication" tab
3. Click "Check Auth Status"

## Troubleshooting

### Backend Issues
- Check if port 3001 is available
- Ensure all dependencies are installed: `npm install`
- Check logs for errors

### Frontend Issues
- The Vite frontend has Node.js compatibility issues
- Use the HTML alternatives provided
- If you need the full Vite setup, try updating Node.js to version 18+

### CORS Issues
- Backend is configured to accept requests from http://localhost:3000
- If using different ports, update the CORS configuration in `backend/src/index.ts`

## Next Steps

1. **Fix Vite Frontend**: Update Node.js version or fix Vite compatibility
2. **Implement Remaining Parsers**: AT, ROA, TRT parsers
3. **Add Analysis Features**: Comprehensive analysis, comparisons
4. **Client Management**: Full CRUD operations
5. **TPS Integration**: Real-time sync with TPS
6. **Deployment**: Deploy to Render or similar platform

## File Structure

```
TIParser/
├── backend/                 # Node.js/Express backend
│   ├── src/
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   └── index.ts        # Server entry point
│   └── package.json
├── frontend/               # React/Vite frontend (has issues)
├── test-frontend.html      # Simple HTML test page
├── simple-react-app.html   # React app using CDN
├── start-servers.sh        # Script to start both servers
└── SETUP_INSTRUCTIONS.md   # This file
```

## Support

If you encounter issues:
1. Check the backend logs for errors
2. Verify all dependencies are installed
3. Ensure ports are not in use by other applications
4. Try the HTML alternatives if Vite continues to have issues 