import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  SearchIcon,
  DownloadIcon,
  FileTextIcon,
  CalendarIcon,
  BookOpenIcon,
  UsersIcon,
  Loader2Icon,
  FilterIcon,
  EyeIcon
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { sessionService, Session } from '../../services/sessionService';
import { toast } from 'sonner';

export const SessionReports = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const isInstructor = user?.role === 'instructor' || user?.role === 'admin';

  useEffect(() => {
    const loadSessions = async () => {
      setLoading(true);
      const all = await sessionService.getAllSessions();
      setSessions(all);
      setLoading(false);
    };

    loadSessions();
  }, []);

  const handleDownload = async (sessionId: string, sessionTitle: string) => {
    setDownloadingId(sessionId);
    try {
      const blob = await sessionService.downloadReport(sessionId);
      if (blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${sessionTitle.replace(/\s+/g, '_')}.html`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Report downloaded successfully!');
      } else {
        toast.error('Failed to download report');
      }
    } catch (error) {
      toast.error('Failed to download report');
    }
    setDownloadingId(null);
  };

  const handleViewReport = (sessionId: string) => {
    navigate(`/dashboard/sessions/${sessionId}/report`);
  };

  // Filter sessions
  const filteredSessions = sessions.filter((session) => {
    const matchesSearch = 
      session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.course.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.courseCode.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Sort by date (most recent first)
  const sortedSessions = [...filteredSessions].sort((a, b) => {
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'live':
        return <Badge variant="danger">Live</Badge>;
      case 'upcoming':
        return <Badge variant="warning">Upcoming</Badge>;
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="py-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2Icon className="h-8 w-8 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Session Reports
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {isInstructor 
            ? 'View and download reports for all your sessions' 
            : 'View and download your session reports'}
        </p>
      </div>

      {/* Search and Filter */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search sessions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            
            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <FilterIcon className="h-5 w-5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="all">All Sessions</option>
                <option value="completed">Completed</option>
                <option value="live">Live</option>
                <option value="upcoming">Upcoming</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sessions List */}
      {sortedSessions.length === 0 ? (
        <Card className="p-12 text-center">
          <FileTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No reports found
          </h3>
          <p className="text-gray-500">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filter' 
              : 'Reports will appear here after you attend sessions'}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {sortedSessions.map((session) => (
            <Card key={session.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  {/* Session Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {session.title}
                      </h3>
                      {getStatusBadge(session.status)}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <BookOpenIcon className="h-4 w-4" />
                        <span>{session.course}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CalendarIcon className="h-4 w-4" />
                        <span>{session.date}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <UsersIcon className="h-4 w-4" />
                        <span>{session.instructor}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400">{session.duration}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      leftIcon={<EyeIcon className="h-4 w-4" />}
                      onClick={() => handleViewReport(session.id)}
                    >
                      View
                    </Button>
                    <Button
                      variant="primary"
                      leftIcon={
                        downloadingId === session.id 
                          ? <Loader2Icon className="h-4 w-4 animate-spin" /> 
                          : <DownloadIcon className="h-4 w-4" />
                      }
                      onClick={() => handleDownload(session.id, session.title)}
                      disabled={downloadingId === session.id}
                    >
                      {downloadingId === session.id ? 'Downloading...' : 'Download'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      <Card className="mt-6">
        <CardContent className="p-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {sessions.length}
              </p>
              <p className="text-sm text-gray-500">Total Sessions</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-600">
                {sessions.filter(s => s.status === 'completed').length}
              </p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {sessions.filter(s => s.status === 'upcoming').length}
              </p>
              <p className="text-sm text-gray-500">Upcoming</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

