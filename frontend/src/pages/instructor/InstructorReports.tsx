import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  FileTextIcon,
  UsersIcon,
  ClockIcon,
  TrendingUpIcon,
  ActivityIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  DownloadIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  XCircleIcon,
  Loader2Icon,
  CalendarIcon,
  BookOpenIcon
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { toast } from 'sonner';

const API_BASE_URL = import.meta.env.VITE_API_URL;

// Types
interface SessionSummary {
  sessionId: string;
  sessionName: string;
  courseName: string;
  courseCode: string;
  date: string;
  time: string;
  duration: string;
  status: string;
  totalStudentsJoined: number;
}

interface AttendanceRecord {
  studentId: string;
  studentName: string;
  studentEmail: string;
  joinTime: string | null;
  leaveTime: string | null;
  durationMinutes: number | null;
  status: string;
}

interface QuizPerformance {
  studentId: string;
  studentName: string;
  studentEmail: string;
  totalQuestions: number;
  correctAnswers: number;
  incorrectAnswers: number;
  unanswered: number;
  score: number;
  averageResponseTime: number | null;
}

interface EngagementData {
  studentId: string;
  studentName: string;
  studentEmail: string;
  quizInteractions: number;
  questionsAnswered: number;
  attendanceDuration: number | null;
  connectionQuality: string;
  engagementLevel: string;
}

export const InstructorReports = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'sessions' | 'attendance' | 'quiz' | 'engagement'>('sessions');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [attendanceData, setAttendanceData] = useState<AttendanceRecord[]>([]);
  const [quizData, setQuizData] = useState<QuizPerformance[]>([]);
  const [engagementData, setEngagementData] = useState<EngagementData[]>([]);
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  
  // Dashboard stats
  const [dashboardStats, setDashboardStats] = useState<any>(null);

  // Fetch sessions on mount
  useEffect(() => {
    fetchSessions();
    fetchDashboardStats();
  }, []);

  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
    'Content-Type': 'application/json'
  });

  const fetchDashboardStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/instructor/reports/dashboard-stats`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setDashboardStats(data.stats);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err);
    }
  };

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/instructor/reports/sessions`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      } else {
        toast.error('Failed to fetch sessions');
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      toast.error('Failed to fetch sessions');
    }
    setLoading(false);
  };

  const fetchAttendance = async (sessionId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/instructor/reports/sessions/${sessionId}/attendance`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setAttendanceData(data.attendance || []);
        setSessionInfo({ name: data.sessionName, date: data.sessionDate });
      }
    } catch (err) {
      console.error('Failed to fetch attendance:', err);
    }
    setLoading(false);
  };

  const fetchQuizPerformance = async (sessionId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/instructor/reports/sessions/${sessionId}/quiz-performance`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setQuizData(data.studentPerformance || []);
        setSessionInfo({ 
          name: data.sessionName, 
          totalQuestions: data.totalQuestions,
          classAverage: data.classAverageScore 
        });
      }
    } catch (err) {
      console.error('Failed to fetch quiz performance:', err);
    }
    setLoading(false);
  };

  const fetchEngagement = async (sessionId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/instructor/reports/sessions/${sessionId}/engagement`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setEngagementData(data.studentEngagement || []);
        setSessionInfo({ 
          name: data.sessionName,
          engagementSummary: data.engagementSummary
        });
      }
    } catch (err) {
      console.error('Failed to fetch engagement:', err);
    }
    setLoading(false);
  };

  const handleSessionSelect = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    if (activeTab === 'attendance') {
      fetchAttendance(sessionId);
    } else if (activeTab === 'quiz') {
      fetchQuizPerformance(sessionId);
    } else if (activeTab === 'engagement') {
      fetchEngagement(sessionId);
    }
  };

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    if (selectedSessionId) {
      if (tab === 'attendance') {
        fetchAttendance(selectedSessionId);
      } else if (tab === 'quiz') {
        fetchQuizPerformance(selectedSessionId);
      } else if (tab === 'engagement') {
        fetchEngagement(selectedSessionId);
      }
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'live':
        return <Badge variant="primary">Live</Badge>;
      default:
        return <Badge variant="warning">Upcoming</Badge>;
    }
  };

  const getEngagementBadge = (level: string) => {
    switch (level) {
      case 'High':
        return <Badge variant="success">High</Badge>;
      case 'Medium':
        return <Badge variant="warning">Medium</Badge>;
      default:
        return <Badge variant="danger">Low</Badge>;
    }
  };

  return (
    <div className="py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Instructor Reports
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            View detailed reports for your sessions
          </p>
        </div>
        <Button
          variant="outline"
          leftIcon={<RefreshCwIcon className="h-4 w-4" />}
          onClick={() => {
            fetchSessions();
            fetchDashboardStats();
          }}
        >
          Refresh
        </Button>
      </div>

      {/* Dashboard Stats */}
      {dashboardStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4 text-center">
            <CalendarIcon className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {dashboardStats.totalSessions}
            </p>
            <p className="text-sm text-gray-500">Total Sessions</p>
          </Card>
          <Card className="p-4 text-center">
            <UsersIcon className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {dashboardStats.totalParticipants}
            </p>
            <p className="text-sm text-gray-500">Total Participants</p>
          </Card>
          <Card className="p-4 text-center">
            <FileTextIcon className="h-8 w-8 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {dashboardStats.totalQuestionsAsked}
            </p>
            <p className="text-sm text-gray-500">Questions Asked</p>
          </Card>
          <Card className="p-4 text-center">
            <TrendingUpIcon className="h-8 w-8 text-orange-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {dashboardStats.averageQuizScore}%
            </p>
            <p className="text-sm text-gray-500">Avg. Quiz Score</p>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-2">
        {[
          { id: 'sessions', label: 'Session Summary', icon: BookOpenIcon },
          { id: 'attendance', label: 'Attendance', icon: ClockIcon },
          { id: 'quiz', label: 'Quiz Performance', icon: FileTextIcon },
          { id: 'engagement', label: 'Engagement', icon: ActivityIcon }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Session List (Left sidebar) */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                Select Session
              </h3>
            </CardHeader>
            <CardContent className="max-h-[500px] overflow-y-auto">
              {loading && sessions.length === 0 ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2Icon className="h-6 w-6 animate-spin text-emerald-600" />
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No sessions found</p>
              ) : (
                <div className="space-y-2">
                  {sessions.map((session) => (
                    <button
                      key={session.sessionId}
                      onClick={() => handleSessionSelect(session.sessionId)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors ${
                        selectedSessionId === session.sessionId
                          ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-900 dark:text-gray-100 text-sm truncate">
                          {session.sessionName}
                        </span>
                        {getStatusBadge(session.status)}
                      </div>
                      <p className="text-xs text-gray-500">{session.courseName}</p>
                      <p className="text-xs text-gray-400">{session.date}</p>
                      <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                        <UsersIcon className="h-3 w-3" />
                        {session.totalStudentsJoined} students
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Report Content (Right side) */}
        <div className="lg:col-span-3">
          {activeTab === 'sessions' && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Session Summary Report
                </h3>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Session</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Course</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Duration</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Students</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {sessions.map((session) => (
                        <tr key={session.sessionId} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                          <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                            {session.sessionName}
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                            {session.courseName}
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                            {session.date}
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                            {session.duration}
                          </td>
                          <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                            {session.totalStudentsJoined}
                          </td>
                          <td className="px-4 py-3">
                            {getStatusBadge(session.status)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'attendance' && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Attendance Report
                    {sessionInfo && <span className="text-sm font-normal text-gray-500 ml-2">- {sessionInfo.name}</span>}
                  </h3>
                  <Badge variant="default">{attendanceData.length} Students</Badge>
                </div>
              </CardHeader>
              <CardContent>
                {!selectedSessionId ? (
                  <div className="text-center py-8 text-gray-500">
                    <ClockIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Select a session to view attendance report</p>
                  </div>
                ) : loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2Icon className="h-6 w-6 animate-spin text-emerald-600" />
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">#</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Student</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Email</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Join Time</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Leave Time</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Duration</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {attendanceData.map((record, idx) => (
                          <tr key={record.studentId} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                            <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                              {record.studentName}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.studentEmail || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.joinTime ? new Date(record.joinTime).toLocaleTimeString() : 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.leaveTime ? new Date(record.leaveTime).toLocaleTimeString() : 'Still in session'}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.durationMinutes !== null ? `${record.durationMinutes} min` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {attendanceData.length === 0 && (
                      <p className="text-center py-8 text-gray-500">No attendance data for this session</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {activeTab === 'quiz' && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Quiz Performance Report
                    {sessionInfo && <span className="text-sm font-normal text-gray-500 ml-2">- {sessionInfo.name}</span>}
                  </h3>
                  {sessionInfo?.classAverage !== undefined && (
                    <Badge variant="primary">Class Avg: {sessionInfo.classAverage}%</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!selectedSessionId ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileTextIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Select a session to view quiz performance</p>
                  </div>
                ) : loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2Icon className="h-6 w-6 animate-spin text-emerald-600" />
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">#</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Student</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Questions</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Correct</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Incorrect</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Score</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Avg. Time</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {quizData.map((record, idx) => (
                          <tr key={record.studentId} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                            <td className="px-4 py-3">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-gray-100">{record.studentName}</p>
                                <p className="text-xs text-gray-500">{record.studentEmail}</p>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.totalQuestions}
                            </td>
                            <td className="px-4 py-3">
                              <span className="inline-flex items-center gap-1 text-green-600">
                                <CheckCircleIcon className="h-4 w-4" />
                                {record.correctAnswers}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="inline-flex items-center gap-1 text-red-600">
                                <XCircleIcon className="h-4 w-4" />
                                {record.incorrectAnswers}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`font-semibold ${
                                record.score >= 80 ? 'text-green-600' : 
                                record.score >= 60 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                {record.score}%
                              </span>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.averageResponseTime ? `${record.averageResponseTime}s` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {quizData.length === 0 && (
                      <p className="text-center py-8 text-gray-500">No quiz data for this session</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {activeTab === 'engagement' && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Engagement Activity Report
                    {sessionInfo && <span className="text-sm font-normal text-gray-500 ml-2">- {sessionInfo.name}</span>}
                  </h3>
                  {sessionInfo?.engagementSummary && (
                    <div className="flex gap-2">
                      <Badge variant="success">{sessionInfo.engagementSummary.highEngagement} High</Badge>
                      <Badge variant="warning">{sessionInfo.engagementSummary.mediumEngagement} Medium</Badge>
                      <Badge variant="danger">{sessionInfo.engagementSummary.lowEngagement} Low</Badge>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!selectedSessionId ? (
                  <div className="text-center py-8 text-gray-500">
                    <ActivityIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Select a session to view engagement report</p>
                  </div>
                ) : loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2Icon className="h-6 w-6 animate-spin text-emerald-600" />
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">#</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Student</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Questions Answered</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Attendance</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Connection</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Engagement</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {engagementData.map((record, idx) => (
                          <tr key={record.studentId} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                            <td className="px-4 py-3">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-gray-100">{record.studentName}</p>
                                <p className="text-xs text-gray-500">{record.studentEmail}</p>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.questionsAnswered}
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                              {record.attendanceDuration !== null ? `${record.attendanceDuration} min` : 'N/A'}
                            </td>
                            <td className="px-4 py-3">
                              <Badge 
                                variant={
                                  record.connectionQuality === 'excellent' || record.connectionQuality === 'good' 
                                    ? 'success' 
                                    : record.connectionQuality === 'fair' 
                                      ? 'warning' 
                                      : 'default'
                                }
                              >
                                {record.connectionQuality || 'Unknown'}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              {getEngagementBadge(record.engagementLevel)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {engagementData.length === 0 && (
                      <p className="text-center py-8 text-gray-500">No engagement data for this session</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default InstructorReports;

