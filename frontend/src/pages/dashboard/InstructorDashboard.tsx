import { Link } from "react-router-dom";
import axios from "axios";
import { useState, useEffect } from "react";

import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { BarChart3Icon, TargetIcon, PlayIcon, CalendarIcon, ClockIcon } from "lucide-react";
import { sessionService, Session } from "../../services/sessionService";
import { Badge } from "../../components/ui/Badge";

export const InstructorDashboard = () => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);

  // ================================
  // ⭐ LOAD REAL SESSIONS FROM BACKEND
  // ================================
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

  // ================================
  // ⭐ JOIN ZOOM MEETING (INSTRUCTOR)
  // ================================
  const handleJoinSession = (session: Session) => {
    if (!session.start_url) {
      alert("❌ Zoom host start URL missing");
      return;
    }
    window.open(session.start_url, '_blank');
  };

  // ================================
  // ⭐ TRIGGER QUESTION FUNCTION
  // ================================
  const handleTriggerQuestion = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL;

      // TEMP MEETING ID (replace with real meeting later)
      const meetingId = "123456789";

      const res = await axios.post(
        `${apiUrl}/api/live/trigger/${meetingId}`
      );

      console.log("Trigger Response:", res.data);
      alert("🎯 Question sent to all students!");
    } catch (error) {
      console.error("Trigger Error:", error);
      alert("❌ Failed to send question");
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Instructor Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Welcome back, {user?.firstName}! Here's an overview of your teaching activities.
          </p>
        </div>

        {/* BUTTON GROUP */}
        <div className="flex gap-3">
          {/* ⭐ Trigger Question Button */}
          <Button
            variant="secondary"
            leftIcon={<TargetIcon className="h-4 w-4" />}
            onClick={handleTriggerQuestion}
          >
            Trigger Question
          </Button>

          <Link to="/dashboard/instructor/analytics">
            <Button variant="primary" leftIcon={<BarChart3Icon className="h-4 w-4" />}>
              View Analytics
            </Button>
          </Link>
        </div>
      </div>

      {/* ================= CARDS SECTION ================= */}
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">

        {/* Active Courses */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5 flex items-center">
            <div className="flex-shrink-0 bg-indigo-500 rounded-md p-3"></div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Active Courses
                </dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">3</div>
                </dd>
              </dl>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <a className="text-sm font-medium text-indigo-700 hover:text-indigo-900" href="#">
              View all
            </a>
          </div>
        </div>

        {/* Upcoming Sessions */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5 flex items-center">
            <div className="flex-shrink-0 bg-green-500 rounded-md p-3"></div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Upcoming Sessions
                </dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">4</div>
                </dd>
              </dl>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <a className="text-sm font-medium text-indigo-700 hover:text-indigo-900" href="#">
              View all
            </a>
          </div>
        </div>

        {/* Total Students */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5 flex items-center">
            <div className="flex-shrink-0 bg-blue-500 rounded-md p-3"></div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Students
                </dt>
                <dd>
                  <div className="text-lg font-medium text-gray-900">124</div>
                </dd>
              </dl>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <a className="text-sm font-medium text-indigo-700 hover:text-indigo-900" href="#">
              View details
            </a>
          </div>
        </div>
      </div>

      {/* ================= REAL UPCOMING SESSION LIST ================= */}
      <div className="mt-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Your Sessions</h2>
          <Link to="/dashboard/sessions">
            <Button variant="outline" size="sm">View All</Button>
          </Link>
        </div>
        
        <div className="mt-2 bg-white shadow overflow-hidden sm:rounded-md">
          {sessions.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              <p>No upcoming sessions</p>
              <Link to="/dashboard/sessions/create">
                <Button variant="primary" className="mt-4">Create Your First Session</Button>
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {sessions.map((session) => (
                <li key={session.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          {session.title}
                        </p>
                        {session.status === 'live' && (
                          <Badge variant="danger" className="bg-red-600 text-white">LIVE</Badge>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-gray-500 flex items-center gap-3">
                        <span className="flex items-center gap-1">
                          <CalendarIcon className="h-4 w-4" />
                          {session.date}
                        </span>
                        <span className="flex items-center gap-1">
                          <ClockIcon className="h-4 w-4" />
                          {session.time}
                        </span>
                      </p>
                      <p className="mt-1 text-xs text-gray-400">
                        {session.course} ({session.courseCode})
                      </p>
                    </div>
                    
                    <div className="ml-4">
                      <Button
                        variant={session.status === 'live' ? 'primary' : 'outline'}
                        size="sm"
                        leftIcon={<PlayIcon className="h-4 w-4" />}
                        onClick={() => handleJoinSession(session)}
                      >
                        {session.status === 'live' ? 'Join Now' : 'Start Meeting'}
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
