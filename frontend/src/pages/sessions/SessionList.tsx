import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';

import {
  SearchIcon,
  CalendarIcon,
  ClockIcon,
  UsersIcon,
  ActivityIcon,
  PlayIcon,
  VideoIcon,
  BookOpenIcon,
  PlusIcon,
  EditIcon,
  FileTextIcon,
  StopCircleIcon,
  Loader2Icon,
  CheckCircleIcon
} from 'lucide-react';

import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';

import { sessionService, Session } from '../../services/sessionService';

export const SessionList = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [endingSessionId, setEndingSessionId] = useState<string | null>(null);
  const [startingSessionId, setStartingSessionId] = useState<string | null>(null);

  const isInstructor = user?.role === 'instructor' || user?.role === 'admin';

  // ---------------------------------------------------
  // ⭐ Load sessions from BACKEND
  // ---------------------------------------------------
  useEffect(() => {
    const loadSessions = async () => {
      const all = await sessionService.getAllSessions();  // FIXED
      setSessions(all);
    };

    loadSessions();

    const interval = setInterval(loadSessions, 30000);
    return () => clearInterval(interval);
  }, []);

  // ---------------------------------------------------
  // ⭐ JOIN LIVE BUTTON
  // ---------------------------------------------------
  const handleJoinSession = (session: Session) => {
    if (isInstructor) {
      if (!session.start_url) {
        alert("❌ Zoom host start URL missing");
        return;
      }
      window.location.href = session.start_url;
      return;
    }

    if (!session.join_url) {
      alert("❌ Zoom join URL missing");
      return;
    }

    window.location.href = session.join_url;
  };

  // ---------------------------------------------------
  // ⭐ START SESSION (Instructor only)
  // ---------------------------------------------------
  const handleStartSession = async (sessionId: string) => {
    setStartingSessionId(sessionId);
    const result = await sessionService.startSession(sessionId);
    if (result.success) {
      toast.success('Session started successfully!');
      // Reload sessions to update status
      const all = await sessionService.getAllSessions();
      setSessions(all);
    } else {
      toast.error(result.message || 'Failed to start session');
    }
    setStartingSessionId(null);
  };

  // ---------------------------------------------------
  // ⭐ END SESSION (Instructor only) - Auto generates report
  // ---------------------------------------------------
  const handleEndSession = async (sessionId: string, sessionTitle: string) => {
    if (!confirm(`Are you sure you want to end "${sessionTitle}"?\n\nThis will:\n• Mark the session as completed\n• Generate the final report\n• Send email notifications to all participants`)) {
      return;
    }
    
    setEndingSessionId(sessionId);
    const result = await sessionService.endSession(sessionId);
    
    if (result.success) {
      toast.success(
        <div>
          <p className="font-medium">Session ended successfully!</p>
          <p className="text-sm text-gray-500">
            {result.participantCount} participants • Report generated • {result.emailsSent} emails sent
          </p>
        </div>
      );
      // Reload sessions to update status
      const all = await sessionService.getAllSessions();
      setSessions(all);
      // Navigate to report
      navigate(`/dashboard/sessions/${sessionId}/report`);
    } else {
      toast.error(result.message || 'Failed to end session');
    }
    setEndingSessionId(null);
  };

  // ---------------------------------------------------
  // FILTER + SEARCH
  // ---------------------------------------------------
  let filtered = sessions.filter((session) => {
    const s = searchTerm.toLowerCase();

    const matches = 
      session.title.toLowerCase().includes(s) ||
      session.course.toLowerCase().includes(s) ||
      session.instructor.toLowerCase().includes(s) ||
      session.courseCode.toLowerCase().includes(s);

    if (!matches) return false;
    if (statusFilter !== 'all' && session.status !== statusFilter) return false;

    return true;
  });

  filtered = [...filtered].sort((a, b) => {
    const order = { live: 0, upcoming: 1, completed: 2 };
    if (order[a.status] !== order[b.status]) {
      return order[a.status] - order[b.status];
    }
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  // ---------------------------------------------------
  // Badges
  // ---------------------------------------------------
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'live':
        return <Badge variant="danger" className="bg-red-600 text-white">LIVE</Badge>;
      case 'upcoming':
        return <Badge variant="success">Upcoming</Badge>;
      case 'completed':
        return <Badge variant="default">Completed</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="py-6">

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Live Sessions</h1>
          <p className="text-sm text-gray-500">Join ongoing and upcoming sessions</p>
        </div>

        {isInstructor && (
          <Button
            variant="primary"
            leftIcon={<PlusIcon className="h-4 w-4" />}
            onClick={() => navigate('/dashboard/sessions/create')}
          >
            Create Session
          </Button>
        )}
      </div>

      {/* Search + Filter */}
      <Card className="mb-6">
        <div className="p-4 flex gap-4">

          <div className="relative flex-1">
            <input
              type="text"
              className="w-full p-2 pl-10 border rounded"
              placeholder="Search sessions…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <SearchIcon className="absolute left-3 top-2 h-5 w-5 text-gray-400" />
          </div>

          <button
            className="px-4 py-2 border rounded bg-white"
            onClick={() => setFilterActive((v) => !v)}
          >
            <CalendarIcon className="inline h-5 w-5 mr-2" />
            Filters
          </button>
        </div>

        {filterActive && (
          <div className="p-4 border-t">
            <label className="block text-sm mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border p-2 rounded w-full"
            >
              <option value="all">All</option>
              <option value="live">Live</option>
              <option value="upcoming">Upcoming</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        )}
      </Card>

      {/* Session Results */}
      {filtered.length === 0 ? (
        <Card className="p-12 text-center">
          <h3 className="text-gray-400">No sessions found</h3>
        </Card>
      ) : (
        <div className="space-y-4">
          {filtered.map((session) => (
            <Card key={session.id} className="p-6">

              <div className="flex justify-between">

                {/* Info */}
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-semibold">{session.title}</h3>
                    {getStatusBadge(session.status)}
                  </div>

                  <p className="text-sm text-gray-600 flex items-center gap-2 mt-2">
                    <BookOpenIcon className="h-4 w-4" />
                    {session.course} ({session.courseCode})
                  </p>

                  <p className="text-sm text-gray-600 flex items-center gap-2 mt-2">
                    <UsersIcon className="h-4 w-4" />
                    {session.instructor}
                  </p>

                  <p className="text-sm text-gray-600 flex items-center gap-2 mt-2">
                    <CalendarIcon className="h-4 w-4" />
                    {session.date}
                  </p>

                  <p className="text-sm text-gray-600 flex items-center gap-2 mt-2">
                    <ClockIcon className="h-4 w-4" />
                    {session.time} ({session.duration})
                  </p>
                </div>

                {/* Buttons */}
                <div className="flex flex-col gap-3">

                  {isInstructor && (
                    <Button
                      variant="outline"
                      leftIcon={<EditIcon className="h-4 w-4" />}
                      onClick={() => navigate(`/dashboard/sessions/${session.id}/edit`)}
                    >
                      Edit
                    </Button>
                  )}

                  {/* START SESSION (Instructor only - for upcoming sessions) */}
                  {isInstructor && session.status === 'upcoming' && (
                    <Button
                      variant="primary"
                      leftIcon={
                        startingSessionId === session.id 
                          ? <Loader2Icon className="h-4 w-4 animate-spin" /> 
                          : <PlayIcon className="h-4 w-4" />
                      }
                      onClick={() => handleStartSession(session.id)}
                      disabled={startingSessionId === session.id}
                    >
                      {startingSessionId === session.id ? 'Starting...' : 'Start Session'}
                    </Button>
                  )}

                  {/* JOIN LIVE */}
                  {session.status === 'live' && (
                    <Button
                      variant="primary"
                      leftIcon={<PlayIcon className="h-4 w-4" />}
                      onClick={() => handleJoinSession(session)}
                    >
                      Join Live
                    </Button>
                  )}

                  {/* END SESSION (Instructor only - for live sessions) */}
                  {isInstructor && session.status === 'live' && (
                    <Button
                      variant="danger"
                      leftIcon={
                        endingSessionId === session.id 
                          ? <Loader2Icon className="h-4 w-4 animate-spin" /> 
                          : <StopCircleIcon className="h-4 w-4" />
                      }
                      onClick={() => handleEndSession(session.id, session.title)}
                      disabled={endingSessionId === session.id}
                    >
                      {endingSessionId === session.id ? 'Ending...' : 'End Session'}
                    </Button>
                  )}

                  {/* VIEW REPORT (for all sessions - students and instructors) */}
                  <Button
                    variant="outline"
                    leftIcon={<FileTextIcon className="h-4 w-4" />}
                    onClick={() => navigate(`/dashboard/sessions/${session.id}/report`)}
                  >
                    View Report
                  </Button>

                  {/* Show completed indicator */}
                  {session.status === 'completed' && (
                    <div className="flex items-center gap-2 text-green-600 text-sm">
                      <CheckCircleIcon className="h-4 w-4" />
                      <span>Report Available</span>
                    </div>
                  )}
                </div>
              </div>

            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
