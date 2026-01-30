# Learning Platform - Complete Project Overview

## 🎯 Project Purpose

A **full-stack adaptive learning platform** with real-time engagement features, built for educational institutions. The platform integrates with Zoom for live virtual classes and uses machine learning to predict and improve student engagement.

---

## 🏗️ Architecture Overview

### Technology Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- React Router (routing)
- Socket.io Client (WebSocket communication)
- Lucide Icons

**Backend:**
- FastAPI (Python async web framework)
- Motor (async MongoDB driver)
- Pydantic (data validation)
- WebSockets (real-time communication)
- XGBoost + scikit-learn (ML engagement prediction)
- PyJWT (authentication)

**Databases:**
- **MongoDB Atlas** (Primary - Source of Truth)
  - Stores all application data
  - Collections: users, sessions, courses, quiz_answers, zoom_events, etc.
- **MySQL** (Backup - Read-Only)
  - Used for auditing and reporting
  - Syncs from MongoDB periodically
  - Enables SQL-based analytics

**Infrastructure:**
- AWS Lambda + API Gateway (Zoom webhook handler)
- AWS CloudFormation (infrastructure as code)
- EC2 (deployment target)
- Nginx (reverse proxy)

---

## 🔑 Core Features

### 1. **User Management & Authentication**
- Role-based access control (Student, Instructor, Admin)
- JWT-based authentication
- Email activation system
- Password reset functionality

### 2. **Course Management**
- Create and manage courses
- Student enrollment
- Course materials upload
- Semester/year tracking

### 3. **Live Sessions with Zoom Integration**
- **Zoom Meeting Creation**: Automatically creates Zoom meetings for sessions
- **Webhook Integration**: Real-time event tracking via AWS Lambda
  - Meeting started/ended
  - Participant joined/left
  - Recording completed
- **Session Types**:
  - Course-linked sessions
  - Standalone sessions (with enrollment keys)

### 4. **Real-Time Quiz System**
- **WebSocket-Based Delivery**: 
  - Students join session rooms via WebSocket
  - Instructors trigger questions to specific sessions
  - Only students in the session room receive questions
- **Features**:
  - Multiple choice questions
  - Time limits
  - Network quality tracking
  - Response time measurement
  - Performance analytics

### 5. **ML-Based Engagement Prediction**
- **XGBoost Model** (99.77% accuracy)
- **Classification**: Active / Moderate / Passive
- **Input Features** (13 features):
  - Answer correctness
  - Response time
  - Network RTT (Round-Trip Time)
  - Jitter and stability
  - Network quality (Poor/Good/Excellent)
  - Question difficulty
  - Speed indicators
- **Output**: Engagement level with confidence scores
- **Use Case**: Adaptive question scheduling based on engagement

### 6. **Student Clustering**
- K-means clustering for performance analysis
- Groups students by quiz performance patterns
- Visualizations for instructors

### 7. **Session Reports & Analytics**
- **Comprehensive Reports**:
  - Attendance tracking (from Zoom webhooks)
  - Quiz performance summaries
  - Engagement metrics
  - Network quality analysis
  - Individual student participation
- **Export**: PDF/CSV download
- **Role-Based Views**:
  - Instructors: Full session analytics
  - Students: Personal performance only

### 8. **Push Notifications**
- Web Push API integration
- Real-time quiz question notifications
- Browser-based notifications

### 9. **AI Question Generation**
- Generate questions from PDF/PPTX files
- Extracts content and creates quiz questions
- Supports multiple difficulty levels

### 10. **Network Quality Monitoring**
- Real-time latency tracking (WebRTC-aware)
- Connection quality indicators
- Network strength tracking per quiz answer

---

## 📁 Project Structure

```
project_fyp-main/
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── auth/          # Authentication components
│   │   │   ├── engagement/    # Engagement indicators
│   │   │   ├── questions/     # Question management
│   │   │   ├── quiz/          # Quiz components
│   │   │   └── sessions/      # Session components
│   │   ├── pages/             # Page components
│   │   │   ├── auth/          # Login, Register, etc.
│   │   │   ├── dashboard/     # Role-based dashboards
│   │   │   ├── courses/       # Course management
│   │   │   ├── sessions/     # Session management
│   │   │   └── reports/       # Reports and analytics
│   │   ├── services/          # API service layer
│   │   ├── hooks/             # Custom React hooks
│   │   └── context/           # React context (Auth, Theme)
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── src/
│   │   ├── routers/           # API route handlers
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── session.py     # Session management
│   │   │   ├── quiz.py        # Quiz endpoints
│   │   │   ├── zoom_webhook.py # Zoom webhook handler
│   │   │   ├── engagement.py  # ML engagement prediction
│   │   │   └── ...
│   │   ├── models/            # Data models (Pydantic)
│   │   ├── services/           # Business logic
│   │   │   ├── ws_manager.py  # WebSocket connection manager
│   │   │   ├── engagement_predictor.py # ML model service
│   │   │   ├── zoom_service.py # Zoom API integration
│   │   │   └── ...
│   │   ├── database/          # Database connections
│   │   │   ├── connection.py  # MongoDB connection
│   │   │   └── mysql_connection.py # MySQL backup
│   │   └── middleware/        # Auth middleware
│   ├── ml_models/             # ML model files
│   │   └── engagement_xgb_hybrid_clean.joblib
│   └── requirements.txt
│
├── aws/                        # AWS infrastructure
│   ├── lambda/                # Lambda function code
│   │   └── zoom_webhook_handler.py
│   ├── cloudformation/        # Infrastructure as code
│   │   └── zoom-webhook-stack.yaml
│   └── [deployment scripts]
│
└── [deployment guides and documentation]
```

---

## 🔄 Data Flow

### 1. **Zoom Webhook Flow**
```
Zoom Meeting Event
    ↓
AWS API Gateway
    ↓
AWS Lambda (zoom_webhook_handler.py)
    ↓
FastAPI Backend (/api/zoom/events)
    ↓
MongoDB (zoom_events, zoom_participants collections)
    ↓
Session Reports (aggregated data)
```

### 2. **Quiz Delivery Flow**
```
Instructor triggers question
    ↓
POST /ws/trigger-session/{session_id}
    ↓
WebSocketManager.broadcast_to_session()
    ↓
Only students in session room receive question
    ↓
Student submits answer
    ↓
POST /api/quiz/submit
    ↓
QuizService processes answer
    ↓
EngagementPredictor predicts engagement
    ↓
MongoDB (quiz_answers collection)
```

### 3. **Engagement Prediction Flow**
```
Quiz Answer Submitted
    ↓
Extract 13 features (correctness, time, network, etc.)
    ↓
EngagementPredictor.predict()
    ↓
XGBoost Model (engagement_xgb_hybrid_clean.joblib)
    ↓
Returns: "Active" / "Moderate" / "Passive" + confidence
    ↓
Stored in session reports
```

---

## 🔌 Key API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/forgot-password` - Request password reset

### Sessions
- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session (creates Zoom meeting)
- `GET /api/sessions/{id}` - Get session details
- `PUT /api/sessions/{id}` - Update session

### Quiz
- `POST /api/quiz/submit` - Submit quiz answer
- `GET /api/quiz/performance/{question_id}` - Get performance stats
- `POST /ws/trigger-session/{session_id}` - Trigger question to session

### Engagement
- `POST /api/engagement/predict` - Predict student engagement
- `GET /api/engagement/model-info` - Get model information

### Zoom
- `POST /api/zoom/events` - Zoom webhook endpoint (via AWS Lambda)
- `GET /api/zoom/participants` - Get meeting participants

### Reports
- `GET /api/session-reports/{session_id}` - Get session report
- `GET /api/instructor-reports/sessions` - Instructor's sessions
- `GET /api/student-reports/performance` - Student's performance

### WebSocket
- `WS /ws/session/{session_id}/{student_id}` - Join session room
- `WS /ws/global/{student_id}` - Global announcements

---

## 🗄️ Database Schema (MongoDB)

### Key Collections

**users**
- User accounts (students, instructors, admins)
- Fields: email, password (hashed), role, status

**sessions**
- Live session information
- Fields: title, course, instructor, date, time, zoomMeetingId, status

**quiz_answers**
- Student quiz responses
- Fields: questionId, studentId, sessionId, answerIndex, timeTaken, networkStrength

**zoom_events**
- Raw Zoom webhook events
- Fields: event type, meeting info, participant data, timestamps

**zoom_participants**
- Participant join/leave tracking
- Fields: meetingId, userId, userName, joinedAt, leftAt, duration

**session_reports**
- Aggregated session analytics
- Fields: sessionId, participants, quiz scores, engagement metrics, students array

**courses**
- Course information
- Fields: courseCode, courseName, instructor, semester, year

---

## 🔐 Security Features

1. **JWT Authentication**: Secure token-based auth
2. **Webhook Signature Verification**: Validates Zoom webhook requests
3. **Role-Based Access Control**: Middleware enforces permissions
4. **CORS Configuration**: Restricted origins
5. **Security Headers**: X-Frame-Options, CSP, etc.
6. **Password Hashing**: Secure password storage

---

## 🚀 Deployment

### Local Development
1. Backend: `cd backend && python main.py` (runs on port 3001)
2. Frontend: `cd frontend && npm run dev` (runs on port 5173)

### AWS Deployment
- **Lambda**: Handles Zoom webhooks
- **EC2**: Hosts FastAPI backend and serves frontend
- **CloudFormation**: Automated infrastructure setup

### Environment Variables

**Backend (.env)**
```
MONGODB_URL=mongodb+srv://...
DATABASE_NAME=learning_platform
ZOOM_CLIENT_ID=...
ZOOM_CLIENT_SECRET=...
ZOOM_WEBHOOK_SECRET=...
JWT_SECRET=...
```

---

## 📊 ML Model Details

**Model**: XGBoost Classifier
**File**: `backend/ml_models/engagement_xgb_hybrid_clean.joblib`
**Accuracy**: 99.77%
**Classes**: Active, Moderate, Passive

**Features** (13 total):
1. Is Correct (0/1)
2. Response Time (seconds)
3. RTT (ms)
4. Jitter (ms)
5. Stability (%)
6. is_fast (0/1)
7. correct_and_fast (0/1)
8. is_very_fast (0/1)
9. poor_network (0/1)
10. excellent_network (0/1)
11. Speed_Ratio
12. Difficulty_Score
13. Network Quality (categorical)

---

## 🎓 User Roles & Permissions

### Student
- View enrolled courses
- Join live sessions
- Answer quiz questions
- View personal performance reports
- Receive push notifications

### Instructor
- Create and manage courses
- Create sessions (auto-creates Zoom meetings)
- Trigger quiz questions during sessions
- View comprehensive session reports
- Access engagement analytics
- Manage questions

### Admin
- All instructor permissions
- User management
- System-wide analytics
- Course management

---

## 🔄 Real-Time Features

1. **WebSocket Connections**:
   - Session-based rooms (quiz delivery)
   - Global connections (announcements)
   - Meeting-based connections (Zoom sessions)

2. **Push Notifications**:
   - Browser push notifications for quiz questions
   - Real-time engagement updates

3. **Live Monitoring**:
   - Network quality indicators
   - Latency tracking
   - Participant count updates

---

## 📝 Key Design Decisions

1. **Hybrid Database**: MongoDB (primary) + MySQL (backup/analytics)
2. **Session-Based WebSockets**: Only joined students receive quizzes
3. **AWS Lambda for Webhooks**: Decouples Zoom integration from main backend
4. **ML Model as Service**: Engagement prediction is a separate service
5. **Role-Based Reports**: Different views for students vs instructors

---

## 🐛 Known Limitations / Future Enhancements

- MySQL backup is optional (system works without it)
- ML model must be manually added to `ml_models/` directory
- Push notifications require HTTPS in production
- Zoom webhook requires AWS setup (or ngrok for local testing)

---

## 📚 Documentation Files

- `README.md` - Main project documentation
- `ZOOM_WEBHOOK_SETUP.md` - Zoom integration guide
- `EC2_DEPLOYMENT_GUIDE.md` - AWS deployment instructions
- `PUSH_NOTIFICATIONS_SETUP.md` - Push notification setup
- `aws/` - AWS-specific deployment guides

---

## 🎯 Project Goals

1. **Real-Time Engagement**: Monitor and improve student engagement during live sessions
2. **Automated Attendance**: Track attendance via Zoom webhooks
3. **Adaptive Learning**: Use ML to personalize question frequency
4. **Comprehensive Analytics**: Detailed reports for instructors and students
5. **Seamless Integration**: Smooth Zoom meeting integration

---

This is a **Final Year Project (FYP)** that demonstrates:
- Full-stack development (React + FastAPI)
- Real-time communication (WebSockets)
- Machine learning integration (XGBoost)
- Cloud infrastructure (AWS)
- Third-party API integration (Zoom)
- Database design (MongoDB + MySQL hybrid)

