import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BellIcon,
  TrendingUpIcon,
  CheckCircleIcon,
  ActivityIcon,
  PlayIcon,
  CalendarIcon,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { useAuth } from "../../context/AuthContext";
import { sessionService, Session } from "../../services/sessionService";

// --------------------------------------
// QUIZ POPUP COMPONENT
// --------------------------------------
const QuizPopup = ({ quiz, onClose }: any) => {
  const { user } = useAuth();
  const [timeLeft, setTimeLeft] = useState<number>(quiz.timeLimit || 20);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL;

  // countdown timer
  useEffect(() => {
    if (timeLeft <= 0) {
      // time over – just close for now
      onClose();
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((t) => t - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, onClose]);

  const handleAnswerClick = async (answerIndex: number) => {
    if (isSubmitting || hasSubmitted) return;
    setIsSubmitting(true);

    try {
      // build payload expected by /api/quiz/submit
      const payload = {
        questionId: quiz.questionId,
        answerIndex,
        timeTaken: (quiz.timeLimit || 20) - timeLeft,
        studentId: user?.id || quiz.studentId || "UNKNOWN",
        sessionId: quiz.sessionId || "GLOBAL",
      };

      const res = await fetch(`${API_BASE_URL}/api/quiz/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        console.error("Submit failed:", await res.text());
        alert("❌ Failed to submit answer");
      } else {
        const data = await res.json();
        console.log("✅ Answer stored:", data);
        // you can later show "Correct/Incorrect" from data.isCorrect if your backend returns it
        alert("✅ Answer submitted!");
      }

      setHasSubmitted(true);
      onClose();
    } catch (err) {
      console.error("Submit error:", err);
      alert("❌ Error submitting answer");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg w-96 shadow-lg">
        <h2 className="text-lg font-bold mb-3">📝 New Quiz</h2>

        <p className="font-medium mb-4">{quiz.question}</p>

        {/* Options */}
        <div className="space-y-2">
          {quiz.options.map((op: string, i: number) => (
            <button
              key={i}
              className="w-full p-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting || hasSubmitted}
              onClick={() => handleAnswerClick(i)}
            >
              {op}
            </button>
          ))}
        </div>

        <div className="mt-4 flex justify-between items-center text-sm text-gray-600">
          <span>Time Left: <span className="font-bold">{timeLeft}s</span></span>
          {isSubmitting && <span>Sending...</span>}
        </div>
      </div>
    </div>
  );
};

// --------------------------------------
// DEFAULT DASHBOARD CONTENT
// --------------------------------------
const recentActivities = [
  {
    id: "1",
    type: "session",
    title: "Database Management Systems",
    course: "CS202: Database Systems",
    date: "2023-10-10",
    engagement: "High",
  },
  {
    id: "2",
    type: "quiz",
    title: "Mid-term Assessment",
    course: "CS301: Machine Learning Fundamentals",
    date: "2023-10-08",
    score: "85%",
  },
];

const performanceData = {
  engagementScore: 85,
  attendanceRate: 92,
  questionsAsked: 12,
  quizAverage: 88,
};

// --------------------------------------
// MAIN COMPONENT
// --------------------------------------
export const StudentDashboard = () => {
  const { user } = useAuth();
  const [incomingQuiz, setIncomingQuiz] = useState<any | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  
  // 🎯 Session WebSocket state - only joined sessions receive quizzes
  const [sessionWs, setSessionWs] = useState<WebSocket | null>(null);
  const [connectedSessionId, setConnectedSessionId] = useState<string | null>(null);

  // ===========================================================
  // ⭐ LOAD REAL SESSIONS FROM BACKEND
  // ===========================================================
  useEffect(() => {
    const loadSessions = async () => {
      const allSessions = await sessionService.getAllSessions();
      // Show only upcoming and live sessions
      const filtered = allSessions.filter(s => s.status === 'upcoming' || s.status === 'live');
      setSessions(filtered.slice(0, 5)); // Show max 5
    };
    loadSessions();
    
    const interval = setInterval(loadSessions, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // ===========================================================
  // 🎯 JOIN ZOOM MEETING + CONNECT TO SESSION WEBSOCKET
  // Only students who click Join will receive quiz questions
  // ===========================================================
  const handleJoinSession = (session: Session) => {
    if (!session.join_url) {
      alert("❌ Zoom join URL missing");
      return;
    }
    
    // Open Zoom meeting
    window.open(session.join_url, '_blank');
    
    // 🎯 Connect to session-specific WebSocket
    const studentId = user?.id || `STUDENT_${Date.now()}`;
    const sessionKey = session.zoomMeetingId || session.id;
    const wsBase = import.meta.env.VITE_WS_URL;
    const sessionWsUrl = `${wsBase}/ws/session/${sessionKey}/${studentId}`;
    
    console.log(`🔗 Connecting to session WebSocket: ${sessionWsUrl}`);
    
    // Close any previous session WebSocket
    if (sessionWs) {
      console.log("🔌 Closing previous session WebSocket");
      sessionWs.close();
    }
    
    // Create new session WebSocket
    const ws = new WebSocket(sessionWsUrl);
    
    ws.onopen = () => {
      console.log(`✅ Connected to session ${sessionKey} WebSocket`);
      setConnectedSessionId(sessionKey);
      alert(`✅ Joined session! You will receive quiz questions.`);
    };
    
    ws.onclose = () => {
      console.log(`🔌 Session ${sessionKey} WebSocket closed`);
      if (connectedSessionId === sessionKey) {
        setConnectedSessionId(null);
      }
    };
    
    ws.onerror = (err) => {
      console.error("Session WS ERROR:", err);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📬 Session WS message:", data);
        
        // Handle quiz questions from session room
        if (data.type === "quiz") {
          console.log("🎯 Quiz received from session room!");
          setIncomingQuiz(data);
        } else if (data.type === "session_joined") {
          console.log("✅ Session join confirmed:", data);
        }
      } catch (e) {
        console.error("Session WS JSON ERROR:", e);
      }
    };
    
    setSessionWs(ws);
  };

  // Cleanup session WebSocket on unmount
  useEffect(() => {
    return () => {
      if (sessionWs) {
        sessionWs.close();
      }
    };
  }, [sessionWs]);

  // ===========================================================
  // ⭐ GLOBAL WebSocket — Receive Notifications (fallback)
  // ===========================================================
  useEffect(() => {
    if (!user) return;

    const studentId = user?.id || `STUDENT_${Date.now()}`;
    const wsBase = import.meta.env.VITE_WS_URL;
    const socketUrl = `${wsBase}/ws/global/${studentId}`;

    console.log("Connecting Global WS:", socketUrl);

    const ws = new WebSocket(socketUrl);

    ws.onopen = () => console.log("🌍 Global WS CONNECTED");
    ws.onclose = () => console.log("❌ Global WS CLOSED");
    ws.onerror = (err) => console.error("Global WS ERROR:", err);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Global WS message:", data);

        // Note: Session-specific quizzes now come via session WebSocket
        // This global WS is kept for announcements and fallback
        if (data.type === "quiz" && !connectedSessionId) {
          // Only show global quizzes if not connected to a session
          console.log("⚠️ Received global quiz (no session connected)");
          // Optionally show: setIncomingQuiz(data);
        }
      } catch (e) {
        console.error("Global WS JSON ERROR:", e);
      }
    };

    return () => ws.close();
  }, [user, connectedSessionId]);

  // ===========================================================
  // UI RENDER
  // ===========================================================
  return (
    <div className="py-6">
      {/* QUIZ POPUP */}
      {incomingQuiz && (
        <QuizPopup quiz={incomingQuiz} onClose={() => setIncomingQuiz(null)} />
      )}

      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">
            Welcome back, {user?.firstName || "Student"}!
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-gray-500">
            Here's what's happening with your courses today.
          </p>
        </div>

        <Link to="/dashboard/student/engagement" className="w-full sm:w-auto">
          <Button
            variant="primary"
            leftIcon={<ActivityIcon className="h-4 w-4" />}
            fullWidth
            className="sm:w-auto"
          >
            View Engagement
          </Button>
        </Link>
      </div>

      {/* Performance Summary */}
      <div className="mb-8 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between">
          <div>
            <h2 className="text-xl font-bold">Your Learning Summary</h2>
            <p className="text-indigo-100 mt-1">
              You are in <span className="font-semibold">Active Participants</span>
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-white bg-opacity-25 text-sm font-medium">
            {performanceData.engagementScore}% Engagement
          </span>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <CheckCircleIcon className="h-6 w-6 text-green-300" />
            <p className="text-sm font-medium">Attendance Rate</p>
            <p className="text-lg font-bold">{performanceData.attendanceRate}%</p>
          </div>

          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <BellIcon className="h-6 w-6 text-yellow-300" />
            <p className="text-sm font-medium">Questions Asked</p>
            <p className="text-lg font-bold">{performanceData.questionsAsked}</p>
          </div>

          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <TrendingUpIcon className="h-6 w-6 text-blue-300" />
            <p className="text-sm font-medium">Quiz Average</p>
            <p className="text-lg font-bold">{performanceData.quizAverage}%</p>
          </div>

          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <p className="text-sm font-medium">Next Class</p>
            <p className="text-lg font-bold">7 days</p>
          </div>
        </div>
      </div>

      {/* Upcoming + Recent */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* REAL Upcoming Sessions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Your Sessions</h3>
            <Link to="/dashboard/sessions">
              <span className="text-sm text-indigo-600 hover:text-indigo-800">View All</span>
            </Link>
          </div>

          {sessions.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              <p className="text-sm">No upcoming sessions</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div key={session.id} className="px-4 py-4 border-t hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-indigo-600">
                        {session.title}
                      </p>
                      {session.status === 'live' && (
                        <Badge variant="danger" className="bg-red-600 text-white text-xs">LIVE</Badge>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {session.course} • {session.instructor}
                    </p>
                    <p className="text-xs text-gray-400 mt-1 flex items-center gap-2">
                      <CalendarIcon className="h-3 w-3" />
                      {session.date} • {session.time}
                    </p>
                  </div>
                  <Button
                    variant={session.status === 'live' ? 'primary' : 'outline'}
                    size="sm"
                    leftIcon={<PlayIcon className="h-4 w-4" />}
                    onClick={() => handleJoinSession(session)}
                  >
                    {session.status === 'live' ? 'Join' : 'Join'}
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Activity */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>

          {recentActivities.map((activity) => (
            <div key={activity.id} className="px-4 py-4 border-t">
              <p className="text-sm font-medium text-indigo-600">
                {activity.title}
              </p>
              <p className="text-xs text-gray-500">{activity.course}</p>
              <p className="text-xs mt-1 text-gray-500">{activity.date}</p>

              {activity.type === "session" && (
                <p className="text-xs mt-1 text-green-600 font-medium">
                  Engagement: {activity.engagement}
                </p>
              )}

              {activity.type === "quiz" && (
                <p className="text-xs mt-1 text-blue-600 font-medium">
                  Score: {activity.score}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
