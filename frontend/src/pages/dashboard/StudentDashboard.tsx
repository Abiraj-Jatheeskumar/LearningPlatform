import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BellIcon,
  TrendingUpIcon,
  CheckCircleIcon,
  ActivityIcon
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

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

export const StudentDashboard = () => {
  const { user } = useAuth();

  // ===========================================================
  // ⭐ GLOBAL WebSocket — Receive Notifications
  // ===========================================================
  useEffect(() => {
    if (!user) return;
  
    // student id safely handled
    const studentId = user?.id || user?.id || `STUDENT_${Date.now()}`;
  
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const wsBase = import.meta.env.VITE_WS_URL || apiUrl.replace(/^http/, "ws");
  
    // 🔥 CORRECT WebSocket URL — Backend requires query params!
    const socketUrl = `${wsBase}/ws/global?meeting_id=GLOBAL&student_id=${studentId}`;
  
    console.log("🔌 Connecting WS:", socketUrl);
  
    const ws = new WebSocket(socketUrl);
  
    ws.onopen = () => console.log("🌍 GLOBAL WS CONNECTED");
    ws.onclose = () => console.log("❌ WS CLOSED");
    ws.onerror = (err) => console.error("⚠️ WS ERROR:", err);
  
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📩 WS MESSAGE:", data);
  
        if (data.type === "quiz") {
          alert("📝 New Quiz:\n" + data.question);
        }
      } catch (e) {
        console.error("WS JSON ERROR:", e);
      }
    };
  
    return () => ws.close();
  }, [user]);
  

  // ===========================================================

  return (
    <div className="py-6">
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

      {/* ================= Performance Summary ================= */}
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

      {/* ================= Upcoming Sessions ================= */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Sessions */}
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

        {/* Recent Activity */}
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
