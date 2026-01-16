import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EngagementIndicator } from '../../components/engagement/EngagementIndicator';
import { 
  BookOpenIcon, UsersIcon, CalendarIcon, ClockIcon, 
  FileTextIcon, VideoIcon, DownloadIcon, TrendingUpIcon,
  ActivityIcon, BarChart3Icon, PlayIcon, CheckCircleIcon
} from 'lucide-react';

export const CourseDetail = () => {
  const { courseId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'sessions' | 'materials' | 'analytics'>('overview');

  // Mock course data with detailed analytics
  const course = {
    id: courseId,
    title: 'Machine Learning Fundamentals',
    code: 'CS301',
    instructor: 'Dr. Jane Smith',
    description: 'An introduction to machine learning concepts and algorithms. This course covers supervised and unsupervised learning, neural networks, and practical applications.',
    startDate: '2023-09-01',
    endDate: '2023-12-15',
    totalSessions: 12,
    completedSessions: 8,
    students: 45,
    progress: 67,
    engagement: 85,
    engagementLevel: 'high' as const,
    averageScore: 88,
    attendanceRate: 92,
    materials: [
      { id: 1, title: 'Introduction to ML', type: 'pdf', size: '2.4 MB', downloads: 42 },
      { id: 2, title: 'Supervised Learning', type: 'pdf', size: '3.1 MB', downloads: 38 },
      { id: 3, title: 'Neural Networks Overview', type: 'video', size: '125 MB', views: 35 },
      { id: 4, title: 'Assignment 1: Linear Regression', type: 'pdf', size: '1.2 MB', downloads: 40 }
    ],
    upcomingSessions: [
      { id: '1', title: 'Neural Networks', date: '2023-10-15', time: '14:00-15:30', status: 'upcoming' },
      { id: '2', title: 'Reinforcement Learning', date: '2023-10-22', time: '14:00-15:30', status: 'upcoming' }
    ],
    pastSessions: [
      { id: '3', title: 'Deep Learning Basics', date: '2023-10-08', time: '14:00-15:30', status: 'completed', engagement: 88 },
      { id: '4', title: 'CNN Architectures', date: '2023-10-01', time: '14:00-15:30', status: 'completed', engagement: 82 }
    ],
    analytics: {
      totalQuestions: 45,
      averageResponseTime: 8.5,
      participationRate: 85,
      quizAverage: 88
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BookOpenIcon },
    { id: 'sessions', label: 'Sessions', icon: CalendarIcon },
    { id: 'materials', label: 'Materials', icon: FileTextIcon },
    { id: 'analytics', label: 'Analytics', icon: BarChart3Icon }
  ];

  return (
    <div className="py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <Link
                to="/dashboard/courses"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                ← Back to Courses
              </Link>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">{course.title}</h1>
            <p className="mt-1 text-lg text-gray-600">Course Code: {course.code}</p>
            <p className="mt-2 text-sm text-gray-500">Instructor: {course.instructor}</p>
          </div>
          <div className="flex space-x-3">
            {course.upcomingSessions.length > 0 && (
              <Button
                variant="primary"
                leftIcon={<PlayIcon className="h-4 w-4" />}
                onClick={() => navigate(`/dashboard/sessions/${course.upcomingSessions[0].id}`)}
              >
                Join Next Session
              </Button>
            )}
            {(user?.role === 'instructor' || user?.role === 'admin') && (
              <Button
                variant="outline"
                leftIcon={<BarChart3Icon className="h-4 w-4" />}
                onClick={() => navigate(`/dashboard/instructor/analytics`)}
              >
                View Analytics
              </Button>
            )}
        </div>
        </div>

        {/* Progress and Engagement */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Course Progress</p>
                <p className="text-2xl font-bold text-gray-900">{course.progress}%</p>
      </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <TrendingUpIcon className="h-6 w-6 text-blue-600" />
        </div>
            </div>
            <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${course.progress}%` }}
              />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm text-gray-600">Your Engagement</p>
              </div>
            </div>
            <EngagementIndicator
              engagementLevel={course.engagementLevel}
              engagementScore={course.engagement}
              showCluster={false}
            />
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">{course.averageScore}%</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <CheckCircleIcon className="h-6 w-6 text-blue-600" />
            </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Description</h3>
                <p className="text-gray-700 leading-relaxed">{course.description}</p>
                
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Start Date</p>
                    <p className="text-sm font-medium text-gray-900">{course.startDate}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">End Date</p>
                    <p className="text-sm font-medium text-gray-900">{course.endDate}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total Sessions</p>
                    <p className="text-sm font-medium text-gray-900">{course.totalSessions}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Enrolled Students</p>
                    <p className="text-sm font-medium text-gray-900">{course.students}</p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="p-4">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg mr-3">
                    <ActivityIcon className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Attendance</p>
                    <p className="text-lg font-bold text-gray-900">{course.attendanceRate}%</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg mr-3">
                    <CheckCircleIcon className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Quiz Average</p>
                    <p className="text-lg font-bold text-gray-900">{course.analytics.quizAverage}%</p>
                  </div>
                </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg mr-3">
                    <ClockIcon className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Response Time</p>
                    <p className="text-lg font-bold text-gray-900">{course.analytics.averageResponseTime}s</p>
          </div>
                    </div>
              </Card>
              <Card className="p-4">
                <div className="flex items-center">
                  <div className="p-2 bg-orange-100 rounded-lg mr-3">
                    <UsersIcon className="h-5 w-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Participation</p>
                    <p className="text-lg font-bold text-gray-900">{course.analytics.participationRate}%</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'sessions' && (
          <div className="space-y-6">
            {/* Upcoming Sessions */}
            {course.upcomingSessions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Sessions</h3>
                <div className="space-y-3">
                  {course.upcomingSessions.map(session => (
                    <Card key={session.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h4 className="text-lg font-semibold text-gray-900">{session.title}</h4>
                            <Badge variant="success">Upcoming</Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <div className="flex items-center">
                              <CalendarIcon className="h-4 w-4 mr-1" />
                              {session.date}
                            </div>
                            <div className="flex items-center">
                              <ClockIcon className="h-4 w-4 mr-1" />
                              {session.time}
                            </div>
                          </div>
                        </div>
                        <Link to={`/dashboard/sessions/${session.id}`}>
                          <Button variant="primary" leftIcon={<PlayIcon className="h-4 w-4" />}>
                            Join
                          </Button>
                        </Link>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Past Sessions */}
            {course.pastSessions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Past Sessions</h3>
                <div className="space-y-3">
                  {course.pastSessions.map(session => (
                    <Card key={session.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h4 className="text-lg font-semibold text-gray-900">{session.title}</h4>
                            <Badge variant="default">Completed</Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                            <div className="flex items-center">
                              <CalendarIcon className="h-4 w-4 mr-1" />
                              {session.date}
                            </div>
                            <div className="flex items-center">
                              <ClockIcon className="h-4 w-4 mr-1" />
                              {session.time}
                            </div>
                            {session.engagement && (
                              <div className="flex items-center">
                                <ActivityIcon className="h-4 w-4 mr-1" />
                                Engagement: {session.engagement}%
                              </div>
                            )}
                          </div>
                        </div>
                        <Link to={`/dashboard/sessions/${session.id}`}>
                          <Button variant="outline">View Recording</Button>
                        </Link>
                      </div>
                    </Card>
                  ))}
          </div>
        </div>
            )}
          </div>
        )}

        {activeTab === 'materials' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Materials</h3>
            <div className="space-y-3">
              {course.materials.map(material => (
                <Card key={material.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      <div className={`p-3 rounded-lg ${
                        material.type === 'pdf' ? 'bg-red-100' : 'bg-blue-100'
                      }`}>
                        {material.type === 'pdf' ? (
                          <FileTextIcon className={`h-6 w-6 ${
                            material.type === 'pdf' ? 'text-red-600' : 'text-blue-600'
                          }`} />
                        ) : (
                          <VideoIcon className="h-6 w-6 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900">{material.title}</h4>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                          <span>{material.size}</span>
                          <span>•</span>
                          <span>
                            {material.type === 'pdf' 
                              ? `${material.downloads} downloads`
                              : `${material.views} views`}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button className="ml-4 p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                      <DownloadIcon className="h-5 w-5" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Analytics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Engagement Metrics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Overall Engagement</span>
                      <span className="text-sm font-semibold text-gray-900">{course.engagement}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${course.engagement}%` }}
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Participation Stats</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Questions Answered</span>
                      <span className="font-semibold text-gray-900">{course.analytics.totalQuestions}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Participation Rate</span>
                      <span className="font-semibold text-gray-900">{course.analytics.participationRate}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Avg Response Time</span>
                      <span className="font-semibold text-gray-900">{course.analytics.averageResponseTime}s</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
