import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpenIcon, CalendarIcon, ClockIcon, BellIcon, TrendingUpIcon, CheckCircleIcon, ActivityIcon } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

const upcomingSessions = [
  {
    id: '1',
    title: 'Introduction to Machine Learning',
    course: 'CS301: Machine Learning Fundamentals',
    instructor: 'Dr. Jane Smith',
    date: '2023-10-15',
    time: '10:00 AM - 11:30 AM',
    status: 'upcoming'
  },
  {
    id: '2',
    title: 'Data Structures and Algorithms',
    course: 'CS201: Algorithms',
    instructor: 'Prof. John Doe',
    date: '2023-10-16',
    time: '2:00 PM - 3:30 PM',
    status: 'upcoming'
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

  // --------------------------
  // ✅ WebSocket Test Code
  // --------------------------
  useEffect(() => {
    const meetingId = "TEST_MEETING";
    const studentId = "TEST_STUDENT";

    const ws = new WebSocket(
      `ws://127.0.0.1:8000/ws/${meetingId}/${studentId}`
    );

    ws.onopen = () => console.log("WS CONNECTED ✔");
    ws.onmessage = (event) => console.log("WS MESSAGE:", event.data);
    ws.onclose = () => console.log("WS CLOSED");
    ws.onerror = (err) => console.log("WS ERROR:", err);

    return () => ws.close();
  }, []);

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

      {/* Performance Summary */}
      <div className="mb-8 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg shadow-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-bold">Your Learning Summary</h2>
            <p className="text-indigo-100 mt-1">
              You're in the{' '}
              <span className="font-semibold">Active Participants</span> cluster
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white bg-opacity-25 text-white">
              {performanceData.engagementScore}% Engagement
            </span>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-6 w-6 mr-2 text-green-300" />
              <div>
                <p className="text-sm font-medium">Attendance Rate</p>
                <p className="text-lg font-bold">
                  {performanceData.attendanceRate}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center">
              <BellIcon className="h-6 w-6 mr-2 text-yellow-300" />
              <div>
                <p className="text-sm font-medium">Questions Asked</p>
                <p className="text-lg font-bold">
                  {performanceData.questionsAsked}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center">
              <TrendingUpIcon className="h-6 w-6 mr-2 text-blue-300" />
              <div>
                <p className="text-sm font-medium">Quiz Average</p>
                <p className="text-lg font-bold">
                  {performanceData.quizAverage}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Next Class</p>
                <p className="text-lg font-bold">7 days</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upcoming Sessions */}
      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* Column 1 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Upcoming Sessions
            </h3>
          </div>

          <div className="divide-y divide-gray-200">
            {upcomingSessions.map((session) => (
              <div key={session.id} className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <p className="text-sm font-medium text-indigo-600 truncate">
                      {session.title}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      {session.course} • {session.instructor}
                    </p>
                  </div>

                  <div className="ml-2 flex-shrink-0 flex">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      {session.date} • {session.time}
                    </span>
                  </div>
                </div>

                <div className="mt-2 flex justify-end">
                  <Link
                    to={`/dashboard/sessions/${session.id}`}
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                  >
                    Join Session
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Column 2 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Recent Activity
            </h3>
          </div>

          <div className="divide-y divide-gray-200">
            {recentActivities.map((activity) => (
              <div key={activity.id} className="px-4 py-4 sm:px-6">
                <div>
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600 truncate">
                      {activity.title}
                    </p>
                    <p className="ml-2 text-xs text-gray-500">
                      {activity.date}
                    </p>
                  </div>

                  <p className="mt-1 text-xs text-gray-500">
                    {activity.course}
                  </p>
                </div>

                <div className="mt-2">
                  {activity.type === 'session' && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Engagement: </span>
                      <span className="font-medium text-green-600">
                        {activity.engagement}
                      </span>
                    </div>
                  )}

                  {activity.type === 'quiz' && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Score: </span>
                      <span className="font-medium text-blue-600">
                        {activity.score}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
