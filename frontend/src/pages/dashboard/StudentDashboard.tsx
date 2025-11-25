import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BellIcon,
  TrendingUpIcon,
  CheckCircleIcon,
  ActivityIcon
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

// --------------------------------------
// QUIZ POPUP COMPONENT
// --------------------------------------
const QuizPopup = ({ quiz, onClose }: any) => {
  const [timeLeft, setTimeLeft] = useState<number>(quiz.timeLimit || 20);


  // countdown timer
  useEffect(() => {
    if (timeLeft <= 0) {
      onClose();
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((t) => t - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft]);

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
              className="w-full p-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              onClick={() => {
                alert(`You selected: ${op}`);
                onClose();
              }}
            >
              {op}
            </button>
          ))}
        </div>

        <div className="mt-4 text-right text-sm text-gray-600">
          Time Left: <span className="font-bold">{timeLeft}s</span>
        </div>
      </div>
    </div>
  );
};

// --------------------------------------
// DEFAULT DASHBOARD CONTENT
// --------------------------------------
const upcomingSessions = [
  {
    id: '1',
    title: 'Introduction to Machine Learning',
    course: 'CS301: Machine Learning Fundamentals',
    instructor: 'Dr. Jane Smith',
    date: '2023-10-15',
    time: '10:00 AM - 11:30 AM'
  },
  {
    id: '2',
    title: 'Data Structures and Algorithms',
    course: 'CS201: Algorithms',
    instructor: 'Prof. John Doe',
    date: '2023-10-16',
    time: '2:00 PM - 3:30 PM'
  }
];

const recentActivities = [
  {
    id: '1',
    type: 'session',
    title: 'Database Management Systems',
    course: 'CS202: Database Systems',
    date: '2023-10-10',
    engagement: 'High'
  },
  {
    id: '2',
    type: 'quiz',
    title: 'Mid-term Assessment',
    course: 'CS301: Machine Learning Fundamentals',
    date: '2023-10-08',
    score: '85%'
  }
];

const performanceData = {
  engagementScore: 85,
  attendanceRate: 92,
  questionsAsked: 12,
  quizAverage: 88
};

// --------------------------------------
// MAIN COMPONENT
// --------------------------------------
export const StudentDashboard = () => {
  const { user } = useAuth();
  const [incomingQuiz, setIncomingQuiz] = useState<any | null>(null);

  // ===========================================================
  // ⭐ GLOBAL WebSocket — Receive Notifications
  // ===========================================================
  useEffect(() => {
    if (!user) return;

    const studentId = user?.id || `STUDENT_${Date.now()}`;

    const wsBase = import.meta.env.VITE_WS_URL;
    const socketUrl = `${wsBase}/ws/global/${studentId}`;

    console.log("Connecting WS:", socketUrl);

    const ws = new WebSocket(socketUrl);

    ws.onopen = () => console.log("🌍 WS CONNECTED");
    ws.onclose = () => console.log("❌ WS CLOSED");
    ws.onerror = (err) => console.error("WS ERROR:", err);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Incoming WS:", data);

        if (data.type === "quiz") {
          setIncomingQuiz(data);
        }

      } catch (e) {
        console.error("WS JSON ERROR:", e);
      }
    };

    return () => ws.close();
  }, [user]);

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
            Welcome back, {user?.firstName || 'Student'}!
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

        {/* Upcoming */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5">
            <h3 className="text-lg font-medium text-gray-900">Upcoming Sessions</h3>
          </div>

          {upcomingSessions.map((session) => (
            <div key={session.id} className="px-4 py-4 border-t">
              <p className="text-sm font-medium text-indigo-600">{session.title}</p>
              <p className="text-xs text-gray-500">
                {session.course} • {session.instructor}
              </p>
              <div className="mt-2 flex justify-end">
                <Link
                  to={`/dashboard/sessions/${session.id}`}
                  className="text-sm font-medium text-indigo-600"
                >
                  Join Session
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Activity */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>

          {recentActivities.map((activity) => (
            <div key={activity.id} className="px-4 py-4 border-t">
              <p className="text-sm font-medium text-indigo-600">{activity.title}</p>
              <p className="text-xs text-gray-500">{activity.course}</p>
              <p className="text-xs mt-1 text-gray-500">{activity.date}</p>

              {activity.type === 'session' && (
                <p className="text-xs mt-1 text-green-600 font-medium">
                  Engagement: {activity.engagement}
                </p>
              )}

              {activity.type === 'quiz' && (
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
