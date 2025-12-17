import React, { useState, useMemo, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { BookOpenIcon, CalendarIcon, MenuIcon, XIcon, HomeIcon, GraduationCapIcon, BellIcon, LogOutIcon, BarChart3Icon, ActivityIcon, ChevronLeftIcon, ChevronRightIcon, TargetIcon, UsersIcon, KeyIcon } from 'lucide-react';

export const DashboardLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    // Get saved state from localStorage or default to false
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved ? JSON.parse(saved) : false;
  });

  // Save sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(sidebarCollapsed));
  }, [sidebarCollapsed]);

  // Get dashboard route based on user role
  const getDashboardRoute = () => {
    if (user?.role) {
      return `/dashboard/${user.role}`;
    }
    return '/dashboard/student';
  };

  // Get user initials for avatar
  const userInitials = useMemo(() => {
    if (user?.firstName && user?.lastName) {
      return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
    }
    return 'U';
  }, [user]);

  // Navigation items based on user role
  const navigationItems = useMemo(() => {
    const baseItems = [
      {
        name: 'Dashboard',
        href: getDashboardRoute(),
        icon: HomeIcon
      },
      {
        name: 'Courses',
        href: '/dashboard/courses',
        icon: BookOpenIcon
      },
      {
        name: 'Sessions',
        href: '/dashboard/sessions',
        icon: CalendarIcon
      }
    ];

    // Add role-specific items
    if (user?.role === 'student') {
      baseItems.push({
        name: 'Enroll',
        href: '/dashboard/student/enrollment',
        icon: KeyIcon
      });
      baseItems.push({
        name: 'My Engagement',
        href: '/dashboard/student/engagement',
        icon: ActivityIcon
      });
    }

    if (user?.role === 'instructor' || user?.role === 'admin') {
      baseItems.push({
        name: 'Analytics',
        href: '/dashboard/instructor/analytics',
        icon: BarChart3Icon
      });
      baseItems.push({
        name: 'Questions',
        href: '/dashboard/instructor/questions',
        icon: TargetIcon
      });
      baseItems.push({
        name: 'Users',
        href: user?.role === 'admin' ? '/dashboard/admin/users' : '/dashboard/instructor/users',
        icon: UsersIcon
      });
    }

    return baseItems;
  }, [user?.role]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  // Check if current path matches the item (including role-based dashboard)
  const isActive = (href: string) => {
    if (href === getDashboardRoute()) {
      return location.pathname === href || location.pathname === `${href}/home`;
    }
    return location.pathname.startsWith(href);
  };

  // Check if profile is active
  const isProfileActive = location.pathname === '/dashboard/profile';

  // Redirect to login if not authenticated (AFTER all hooks)
  if (!isLoading && !isAuthenticated) {
    navigate('/login');
    return null;
  }

  // Show loading state while checking authentication (AFTER all hooks)
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }
  return <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`md:hidden ${sidebarOpen ? 'fixed inset-0 flex z-40' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 transition-all duration-300 shadow-2xl">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button className="ml-1 flex items-center justify-center h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white transition-colors" onClick={() => setSidebarOpen(false)}>
              <XIcon className="h-6 w-6 text-white" aria-hidden="true" />
            </button>
          </div>
          <div className="flex-1 h-0 pt-6 pb-4 overflow-y-auto">
            {/* Logo/Brand Section */}
            <div className="flex-shrink-0 flex items-center px-6 mb-8">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
                  <GraduationCapIcon className="h-7 w-7 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Learning Platform</h2>
                  <p className="text-xs text-indigo-200">Smart Education</p>
                </div>
              </div>
            </div>
            
            {/* Navigation */}
            <nav className="px-3 space-y-1">
              {navigationItems.map(item => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    group flex items-center px-4 py-3 text-base font-medium rounded-xl transition-all duration-200
                    ${
                      isActive(item.href)
                        ? 'bg-white/20 text-white shadow-lg backdrop-blur-sm border border-white/30'
                        : 'text-indigo-100 hover:bg-white/10 hover:text-white'
                    }
                  `}
                >
                  <item.icon className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive(item.href) ? 'text-white' : 'text-indigo-200'}`} aria-hidden="true" />
                  <span className="font-medium">{item.name}</span>
                  {isActive(item.href) && (
                    <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                  )}
                </Link>
              ))}
            </nav>
          </div>
          
          {/* User Profile Section - Mobile */}
          <Link
            to="/dashboard/profile"
            onClick={() => setSidebarOpen(false)}
            className={`flex-shrink-0 border-t border-white/20 p-4 backdrop-blur-sm transition-colors ${
              isProfileActive ? 'bg-white/15' : 'bg-white/5 hover:bg-white/10'
            }`}
          >
            <div className="flex items-center w-full">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-white/30 to-white/10 flex items-center justify-center text-white font-bold text-sm shadow-lg border border-white/20">
                {userInitials}
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">
                  {user?.firstName} {user?.lastName}
                </p>
                <div className="flex items-center space-x-1 mt-0.5">
                  <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                  <p className="text-xs font-medium text-indigo-200 capitalize truncate">
                    {user?.role || 'User'}
                  </p>
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>
      {/* Static sidebar for desktop */}
      <div className={`hidden md:flex md:flex-shrink-0 transition-all duration-300 ${sidebarCollapsed ? 'w-20' : 'w-72'}`}>
        <div className="flex flex-col w-full relative">
          <div className="flex flex-col h-0 flex-1 bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 shadow-2xl">
            <div className="flex-1 flex flex-col pt-6 pb-4 overflow-y-auto">
              {/* Logo/Brand Section */}
              <div className={`flex-shrink-0 flex items-center mb-8 transition-all duration-300 ${sidebarCollapsed ? 'px-3 justify-center' : 'px-6'}`}>
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 bg-white/20 rounded-xl backdrop-blur-sm shadow-lg">
                    <GraduationCapIcon className="h-7 w-7 text-white" />
                  </div>
                  {!sidebarCollapsed && (
                    <div className="transition-opacity duration-300">
                      <h2 className="text-xl font-bold text-white">Learning Platform</h2>
                      <p className="text-xs text-indigo-200 font-medium">Smart Education</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Navigation */}
              <nav className={`flex-1 space-y-1.5 transition-all duration-300 ${sidebarCollapsed ? 'px-2' : 'px-3'}`}>
                {navigationItems.map(item => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      group flex items-center rounded-xl transition-all duration-200
                      ${
                        isActive(item.href)
                          ? 'bg-white/20 text-white shadow-lg backdrop-blur-sm border border-white/30'
                          : 'text-indigo-100 hover:bg-white/10 hover:text-white hover:shadow-md'
                      }
                      ${sidebarCollapsed ? 'px-3 py-3 justify-center' : 'px-4 py-3'}
                    `}
                    title={sidebarCollapsed ? item.name : undefined}
                  >
                    <item.icon
                      className={`flex-shrink-0 transition-colors ${
                        isActive(item.href) ? 'text-white' : 'text-indigo-200 group-hover:text-white'
                      } ${sidebarCollapsed ? 'h-6 w-6' : 'mr-3 h-5 w-5'}`}
                      aria-hidden="true"
                    />
                    {!sidebarCollapsed && (
                      <>
                        <span className="font-semibold text-sm">{item.name}</span>
                        {isActive(item.href) && (
                          <div className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse"></div>
                        )}
                      </>
                    )}
                  </Link>
                ))}
              </nav>
            </div>

            {/* User Profile Section */}
            <Link
              to="/dashboard/profile"
              className={`flex-shrink-0 border-t border-white/20 backdrop-blur-sm transition-colors cursor-pointer ${
                isProfileActive ? 'bg-white/15' : 'bg-white/5 hover:bg-white/10'
              } ${sidebarCollapsed ? 'p-3' : 'p-4'}`}
              title={sidebarCollapsed ? 'Profile' : undefined}
            >
              <div className={`flex items-center transition-all duration-300 ${sidebarCollapsed ? 'justify-center' : ''}`}>
                <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-white/30 to-white/10 flex items-center justify-center text-white font-bold text-sm shadow-lg border border-white/20 flex-shrink-0">
                  {userInitials}
                </div>
                {!sidebarCollapsed && (
                  <div className="ml-3 flex-1 min-w-0">
                    <p className="text-sm font-semibold text-white truncate">
                      {user?.firstName} {user?.lastName}
                    </p>
                    <div className="flex items-center space-x-1 mt-0.5">
                      <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                      <p className="text-xs font-medium text-indigo-200 capitalize truncate">
                        {user?.role || 'User'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </Link>

            {/* Toggle Button */}
            <button
              onClick={toggleSidebar}
              className="absolute -right-3 top-1/2 transform -translate-y-1/2 z-10 p-1.5 bg-white rounded-full shadow-lg border-2 border-indigo-600 hover:bg-indigo-50 transition-colors"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? (
                <ChevronRightIcon className="h-4 w-4 text-indigo-600" />
              ) : (
                <ChevronLeftIcon className="h-4 w-4 text-indigo-600" />
              )}
            </button>
          </div>
        </div>
      </div>
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Top navigation bar */}
        <div className="relative z-10 flex-shrink-0 flex h-16 bg-white shadow">
          <button className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 md:hidden" onClick={() => setSidebarOpen(true)}>
            <MenuIcon className="h-6 w-6" aria-hidden="true" />
          </button>
            <div className="flex-1 px-2 sm:px-4 flex justify-between items-center">
                <div className="flex items-center">
                  <span className="text-base sm:text-lg font-semibold text-gray-900 hidden sm:block">
                    {user?.role === 'student' && 'Student Dashboard'}
                    {user?.role === 'instructor' && 'Instructor Dashboard'}
                    {user?.role === 'admin' && 'Admin Dashboard'}
                  </span>
                  <span className="text-sm font-semibold text-gray-900 sm:hidden">
                    {user?.role === 'student' && 'Student'}
                    {user?.role === 'instructor' && 'Instructor'}
                    {user?.role === 'admin' && 'Admin'}
                  </span>
                </div>
                <div className="ml-2 sm:ml-4 flex items-center md:ml-6 space-x-1 sm:space-x-2">
              {/* Notifications Button */}
              <button 
                className="p-2 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500" 
                aria-label="View notifications"
              >
                <BellIcon className="h-5 w-5" />
              </button>
              
              {/* User Menu Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold text-sm">
                    {userInitials}
                  </div>
                  <span className="hidden md:block text-sm font-medium text-gray-700">
                    {user?.firstName} {user?.lastName}
                  </span>
                </button>

                {/* Dropdown Menu */}
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setUserMenuOpen(false)}
                    ></div>
                    <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
                      <div className="py-1">
                        <div className="px-4 py-3 border-b border-gray-200">
                          <p className="text-sm font-medium text-gray-900">
                            {user?.firstName} {user?.lastName}
                          </p>
                          <p className="text-xs text-gray-500 capitalize mt-1">
                            {user?.role || 'User'}
                          </p>
                        </div>
                        <button
                          onClick={handleLogout}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                        >
                          <LogOutIcon className="h-4 w-4" />
                          <span>Logout</span>
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Logout Button (Mobile - always visible) */}
              <button
                onClick={handleLogout}
                className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                aria-label="Logout"
              >
                <LogOutIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6 h-full">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 h-full">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>;
};