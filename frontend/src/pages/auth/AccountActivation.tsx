import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { authService } from '../../services/authService';
import { CheckCircle2, XCircle, Loader2, Mail, ArrowRight } from 'lucide-react';

export const AccountActivation = () => {
  const navigate = useNavigate();
  const { token } = useParams();
  const [isLoading, setIsLoading] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const activate = async () => {
      if (!token) {
        setError('Invalid activation link');
        setIsLoading(false);
        return;
      }
      
      try {
        const response = await authService.verifyEmail(token);
        setIsSuccess(response.success);
        
        // Auto-redirect to login after 3 seconds on success
        if (response.success) {
          setTimeout(() => {
            navigate('/login', { 
              state: { 
                message: 'Email verified successfully! Please sign in.',
                verified: true 
              } 
            });
          }, 3000);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to activate account');
      } finally {
        setIsLoading(false);
      }
    };
    
    activate();
  }, [token, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-blue-100 to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 via-blue-600 to-blue-600 px-8 py-10 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full mb-4">
              {isLoading ? (
                <Loader2 className="w-10 h-10 text-white animate-spin" />
              ) : isSuccess ? (
                <CheckCircle2 className="w-10 h-10 text-white" />
              ) : (
                <XCircle className="w-10 h-10 text-white" />
              )}
            </div>
            <h1 className="text-2xl font-bold text-white">
              {isLoading 
                ? 'Verifying...' 
                : isSuccess 
                  ? 'Email Verified!' 
                  : 'Verification Failed'}
            </h1>
          </div>

          {/* Content */}
          <div className="px-8 py-10">
            {isLoading ? (
              <div className="text-center">
                <p className="text-gray-600 dark:text-gray-400">
                  Please wait while we verify your email address...
                </p>
                <div className="mt-6 flex justify-center">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            ) : isSuccess ? (
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
                  <CheckCircle2 className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Welcome to Class Pulse!
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Your email has been verified successfully. You can now sign in to your account and start learning!
                </p>
                <p className="text-sm text-blue-600 dark:text-blue-400 mb-6">
                  Redirecting to login in 3 seconds...
                </p>
                <Link
                  to="/login"
                  className="
                    inline-flex items-center justify-center gap-2 w-full py-4 px-6 rounded-xl
                    font-semibold text-white
                    bg-gradient-to-r from-blue-500 via-blue-600 to-blue-600 
                    hover:from-blue-600 hover:via-blue-700 hover:to-blue-700
                    transform hover:scale-[1.02] active:scale-[0.98]
                    transition-all duration-200
                    shadow-lg shadow-blue-500/30
                    group
                  "
                >
                  Sign in now
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            ) : (
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
                  <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Verification Failed
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  {error || 'The verification link is invalid or has expired.'}
                </p>
                
                <div className="space-y-3">
                  <Link
                    to="/login"
                    className="
                      flex items-center justify-center gap-2 w-full py-3 px-6 rounded-xl
                      font-semibold text-gray-700 dark:text-gray-200
                      bg-gray-100 dark:bg-gray-700
                      hover:bg-gray-200 dark:hover:bg-gray-600
                      transition-all duration-200
                    "
                  >
                    <Mail className="w-5 h-5" />
                    Request new verification link
                  </Link>
                  <Link
                    to="/login"
                    className="
                      flex items-center justify-center gap-2 w-full py-3 px-6 rounded-xl
                      font-medium text-blue-600 dark:text-blue-400
                      hover:bg-blue-50 dark:hover:bg-blue-900/20
                      transition-all duration-200
                    "
                  >
                    Return to login
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          © {new Date().getFullYear()} Class Pulse. All rights reserved.
        </p>
      </div>
    </div>
  );
};
