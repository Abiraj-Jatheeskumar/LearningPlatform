/**
 * QuestionNotificationPopup Component
 * Shows a popup notification when instructor triggers a question
 */
import React, { useState, useEffect } from 'react';
import { AlertCircleIcon, ClockIcon, XIcon } from 'lucide-react';
import { Button } from '../ui/Button';

export interface NotificationData {
  sessionToken: string;
  question: string;
  options: string[];
  timeLimit: number;
  questionUrl: string;
  instructorName: string;
  triggeredAt: string;
}

interface QuestionNotificationPopupProps {
  notification: NotificationData;
  onClose: () => void;
  onAnswer: () => void;
}

export const QuestionNotificationPopup: React.FC<QuestionNotificationPopupProps> = ({
  notification,
  onClose,
  onAnswer,
}) => {
  const [timeRemaining, setTimeRemaining] = useState(notification.timeLimit);
  const [isVisible, setIsVisible] = useState(false);

  // Animate in
  useEffect(() => {
    setTimeout(() => setIsVisible(true), 50);
  }, []);

  // Countdown timer
  useEffect(() => {
    if (timeRemaining <= 0) return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeRemaining]);

  const handleAnswer = () => {
    onAnswer();
    // Redirect to question page
    window.location.href = notification.questionUrl;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black transition-opacity duration-300 z-50 ${
          isVisible ? 'bg-opacity-50' : 'bg-opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Popup */}
      <div
        className={`fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg mx-4 transition-all duration-300 ${
          isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        }`}
      >
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border-4 border-indigo-500 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="bg-white p-2 rounded-full animate-bounce">
                  <AlertCircleIcon className="h-6 w-6 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-white font-bold text-lg">
                    🎯 You Got a Quiz!
                  </h3>
                  <p className="text-indigo-100 text-sm">
                    From {notification.instructorName}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-1 transition-colors"
                aria-label="Close"
              >
                <XIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Time Remaining */}
            <div className="flex items-center justify-center space-x-2 mb-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
              <ClockIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {formatTime(timeRemaining)}
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                remaining
              </span>
            </div>

            {/* Question Preview */}
            <div className="mb-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Question:
              </p>
              <p className="text-gray-900 dark:text-gray-100 font-medium line-clamp-3">
                {notification.question}
              </p>
            </div>

            {/* Options Count */}
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              {notification.options.length} answer options
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <Button
                variant="primary"
                className="flex-1 py-3 text-lg font-semibold animate-pulse"
                onClick={handleAnswer}
              >
                Answer Now! 🚀
              </Button>
              <Button
                variant="outline"
                onClick={onClose}
                className="px-4"
              >
                Later
              </Button>
            </div>

            {/* Note */}
            <p className="mt-4 text-xs text-center text-gray-500 dark:text-gray-400">
              💡 Your instructor just sent you a quiz question! Click "Answer Now" to start.
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

