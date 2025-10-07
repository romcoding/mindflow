# MindFlow - Personal Productivity & Relationship Management

A comprehensive full-stack application for managing tasks, stakeholders, and notes with intelligent content categorization and voice input capabilities.

## 🚀 Features

### Core Functionality
- **Intelligent Content Categorization**: Automatically analyzes input to determine if it's a task, note, or stakeholder information
- **Voice Input Integration**: Full Web Speech API implementation with real-time transcription
- **Task Management**: Priority-based task organization with smart due date extraction
- **Stakeholder Mapping**: Interactive relationship management with influence/interest matrix
- **Secure Authentication**: JWT-based authentication with refresh tokens
- **Responsive Design**: Works seamlessly on mobile phones and laptops

### Advanced Features
- **Smart Analysis**: Extracts priorities, due dates, and stakeholder names from natural language
- **Relationship Tracking**: Comprehensive stakeholder profiles with personal and professional information
- **Cross-Device Sync**: Cloud-based storage accessible from anywhere
- **Real-time Updates**: Live synchronization across all devices

## 🏗️ Architecture

### Backend (Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT with Flask-JWT-Extended
- **API**: RESTful API with comprehensive endpoints
- **Security**: Password hashing with bcrypt, CORS protection

### Frontend (React)
- **Framework**: React 19 with Vite
- **UI Library**: shadcn/ui with Tailwind CSS
- **State Management**: React Query for server state
- **Authentication**: Context-based auth with automatic token refresh
- **Icons**: Lucide React icons

## 📁 Project Structure

```
mindflow/
├── mindflow-backend/          # Flask API server
│   ├── src/
│   │   ├── models/           # Database models
│   │   ├── routes/           # API endpoints
│   │   └── main.py          # Application entry point
│   ├── venv/                # Python virtual environment
│   └── requirements.txt     # Python dependencies
├── mindflow-frontend/        # React application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities and API client
│   │   └── App.jsx         # Main application component
│   └── package.json        # Node.js dependencies
└── README.md               # This file
```

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm (recommended) or npm

### Backend Setup
```bash
cd mindflow-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Frontend Setup
```bash
cd mindflow-frontend
pnpm install
pnpm run dev
```

### Environment Variables

#### Backend (.env)
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URL=postgresql://user:password@host:port/database  # For production
```

#### Frontend (.env.local)
```env
VITE_API_URL=http://localhost:5000/api  # For development
```

## 🚀 Deployment

### Backend (Render)
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r mindflow-backend/requirements.txt`
4. Set start command: `cd mindflow-backend && python src/main.py`
5. Add environment variables (DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY)

### Frontend (Vercel)
1. Connect your GitHub repository to Vercel
2. Set root directory to `mindflow-frontend`
3. Build command: `pnpm run build`
4. Output directory: `dist`
5. Add environment variables (VITE_API_URL)

### Database (Render PostgreSQL)
1. Create a PostgreSQL database on Render
2. Copy the connection string to your backend environment variables

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Task Endpoints
- `GET /api/tasks` - Get user tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task
- `PATCH /api/tasks/:id/toggle` - Toggle task completion

### Stakeholder Endpoints
- `GET /api/stakeholders` - Get user stakeholders
- `POST /api/stakeholders` - Create new stakeholder
- `PUT /api/stakeholders/:id` - Update stakeholder
- `DELETE /api/stakeholders/:id` - Delete stakeholder

### Notes Endpoints
- `GET /api/notes` - Get user notes
- `POST /api/notes` - Create new note
- `PUT /api/notes/:id` - Update note
- `DELETE /api/notes/:id` - Delete note

## 🔒 Security Features

- **Password Security**: Bcrypt hashing with salt
- **JWT Authentication**: Secure token-based authentication
- **Token Refresh**: Automatic token renewal
- **CORS Protection**: Configured for specific origins
- **Input Validation**: Comprehensive server-side validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## 🎯 Usage Examples

### Quick Add with Voice Input
1. Click the "QUICK ADD" button
2. Speak or type your thought
3. AI automatically categorizes as task, stakeholder, or note
4. Review the analysis and save

### Task Management
- Create tasks with priorities and due dates
- Toggle completion status
- Filter by priority, completion status, or due date

### Stakeholder Management
- Add comprehensive contact information
- Track relationship sentiment and influence levels
- Visualize stakeholder matrix
- Maintain contact history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with modern web technologies
- UI components from shadcn/ui
- Icons from Lucide React
- Styling with Tailwind CSS
