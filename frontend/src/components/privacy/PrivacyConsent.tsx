import React, { useEffect, useState } from 'react';
import { Button } from '../ui/Button';
import { ShieldIcon, InfoIcon } from 'lucide-react';
interface PrivacyConsentProps {
  onAccept: () => void;
  onDecline: () => void;
}
export const PrivacyConsent: React.FC<PrivacyConsentProps> = ({
  onAccept,
  onDecline
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [preferences, setPreferences] = useState({
    essential: true,
    analytics: true,
    engagement: true,
    performance: true
  });
  useEffect(() => {
    // Check if user has already given consent
    const hasConsent = localStorage.getItem('privacyConsent');
    if (!hasConsent) {
      setIsOpen(true);
    }
  }, []);
  const handleAccept = () => {
    localStorage.setItem('privacyConsent', JSON.stringify(preferences));
    setIsOpen(false);
    onAccept();
  };
  const handleDecline = () => {
    setIsOpen(false);
    onDecline();
  };
  const handleTogglePreference = (key: keyof typeof preferences) => {
    if (key === 'essential') return; // Essential cannot be toggled
    setPreferences(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };
  if (!isOpen) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
        <div className="p-6 bg-gradient-to-r from-indigo-500 to-purple-600 text-white flex items-center">
          <ShieldIcon className="h-8 w-8 mr-3" />
          <div>
            <h2 className="text-xl font-bold">Privacy & Data Consent</h2>
            <p className="text-sm opacity-90">GDPR and PDPA Compliant</p>
          </div>
        </div>
        <div className="p-6">
          <p className="text-gray-700 dark:text-gray-300">
            app name uses AI technology to improve your learning experience.
            Before proceeding, please review and customize your data sharing
            preferences.
          </p>
          <div className="mt-6 space-y-4">
            <div className="flex items-start p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center h-5">
                <input id="essential" type="checkbox" checked={preferences.essential} disabled className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded" />
              </div>
              <div className="ml-3">
                <label htmlFor="essential" className="font-medium text-gray-800 dark:text-gray-200">
                  Essential Data{' '}
                  <span className="text-xs text-gray-500">(Required)</span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Basic account information and system functionality.
                </p>
              </div>
            </div>
            <div className="flex items-start p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center h-5">
                <input id="analytics" type="checkbox" checked={preferences.analytics} onChange={() => handleTogglePreference('analytics')} className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded" />
              </div>
              <div className="ml-3">
                <label htmlFor="analytics" className="font-medium text-gray-800 dark:text-gray-200">
                  Analytics Data
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Usage patterns to improve our platform and features.
                </p>
              </div>
            </div>
            <div className="flex items-start p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center h-5">
                <input id="engagement" type="checkbox" checked={preferences.engagement} onChange={() => handleTogglePreference('engagement')} className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded" />
              </div>
              <div className="ml-3">
                <label htmlFor="engagement" className="font-medium text-gray-800 dark:text-gray-200">
                  Engagement Tracking
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  AI-powered analysis of your participation during live
                  sessions.
                </p>
              </div>
            </div>
            <div className="flex items-start p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center h-5">
                <input id="performance" type="checkbox" checked={preferences.performance} onChange={() => handleTogglePreference('performance')} className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded" />
              </div>
              <div className="ml-3">
                <label htmlFor="performance" className="font-medium text-gray-800 dark:text-gray-200">
                  Performance Data
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Learning patterns for personalized feedback and
                  recommendations.
                </p>
              </div>
            </div>
          </div>
          <div className="mt-6 flex items-center text-sm">
            <InfoIcon className="h-4 w-4 text-gray-500 mr-2" />
            <p className="text-gray-500 dark:text-gray-400">
              You can change these settings anytime in your account preferences.
            </p>
          </div>
        </div>
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600 flex justify-end space-x-3">
          <Button variant="outline" onClick={handleDecline}>
            Decline
          </Button>
          <Button variant="primary" onClick={handleAccept}>
            Accept Selected
          </Button>
        </div>
      </div>
    </div>;
};
