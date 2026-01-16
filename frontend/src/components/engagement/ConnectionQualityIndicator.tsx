/**
 * ConnectionQualityIndicator Component
 * =====================================
 * 
 * Visual indicator for WebRTC-aware connection quality during live Zoom sessions.
 * 
 * This component displays the current network connection quality based on
 * round-trip time measurements. It helps students and instructors understand
 * potential connectivity issues that may affect engagement metrics.
 * 
 * The connection quality information is used contextually in engagement
 * analysis to avoid misclassifying students with poor network conditions
 * as disengaged.
 */

import React, { useState } from 'react';
import { 
  Wifi, 
  WifiOff, 
  Signal, 
  SignalLow, 
  SignalMedium, 
  SignalHigh,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  Activity
} from 'lucide-react';
import { ConnectionQuality, LatencyStats } from '../../hooks/useLatencyMonitor';

interface ConnectionQualityIndicatorProps {
  quality: ConnectionQuality;
  stats: LatencyStats;
  currentRtt: number | null;
  isMonitoring: boolean;
  compact?: boolean;
  showDetails?: boolean;
  className?: string;
}

export const ConnectionQualityIndicator: React.FC<ConnectionQualityIndicatorProps> = ({
  quality,
  stats,
  currentRtt,
  isMonitoring,
  compact = false,
  showDetails: initialShowDetails = false,
  className = ''
}) => {
  const [showDetails, setShowDetails] = useState(initialShowDetails);

  /**
   * Get the appropriate icon based on connection quality
   */
  const getQualityIcon = () => {
    if (!isMonitoring) {
      return <WifiOff className="h-4 w-4 text-gray-400" />;
    }

    switch (quality) {
      case 'excellent':
        return <SignalHigh className="h-4 w-4 text-blue-500" />;
      case 'good':
        return <Signal className="h-4 w-4 text-blue-400" />;
      case 'fair':
        return <SignalMedium className="h-4 w-4 text-yellow-500" />;
      case 'poor':
        return <SignalLow className="h-4 w-4 text-orange-500" />;
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Wifi className="h-4 w-4 text-gray-400" />;
    }
  };

  /**
   * Get quality label
   */
  const getQualityLabel = (): string => {
    if (!isMonitoring) return 'Not monitoring';
    
    switch (quality) {
      case 'excellent': return 'Excellent';
      case 'good': return 'Good';
      case 'fair': return 'Fair';
      case 'poor': return 'Poor';
      case 'critical': return 'Critical';
      default: return 'Unknown';
    }
  };

  /**
   * Get quality color classes
   */
  const getQualityColorClasses = () => {
    switch (quality) {
      case 'excellent':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-200 dark:border-blue-800';
      case 'good':
        return 'bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 border-blue-200 dark:border-blue-800';
      case 'fair':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 border-yellow-200 dark:border-yellow-800';
      case 'poor':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 border-orange-200 dark:border-orange-800';
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-200 dark:border-red-800';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700';
    }
  };

  /**
   * Get warning message for poor connections
   */
  const getWarningMessage = (): string | null => {
    if (quality === 'poor') {
      return 'Connection issues detected. Your engagement metrics may be affected.';
    }
    if (quality === 'critical') {
      return 'Severe connection issues. Engagement analysis will consider technical difficulties.';
    }
    return null;
  };

  /**
   * Get signal bars visualization
   */
  const getSignalBars = () => {
    const barCount = 4;
    let activeCount = 0;

    switch (quality) {
      case 'excellent': activeCount = 4; break;
      case 'good': activeCount = 3; break;
      case 'fair': activeCount = 2; break;
      case 'poor': activeCount = 1; break;
      case 'critical': activeCount = 0; break;
      default: activeCount = 0;
    }

    const getBarColor = (index: number) => {
      if (!isMonitoring || index >= activeCount) return 'bg-gray-300 dark:bg-gray-600';
      if (activeCount >= 3) return 'bg-blue-500';
      if (activeCount === 2) return 'bg-yellow-500';
      return 'bg-red-500';
    };

    return (
      <div className="flex items-end space-x-0.5">
        {Array.from({ length: barCount }).map((_, i) => (
          <div
            key={i}
            className={`w-1 rounded-sm transition-all duration-300 ${getBarColor(i)}`}
            style={{ height: `${(i + 1) * 3 + 4}px` }}
          />
        ))}
      </div>
    );
  };

  // Compact version for inline display
  if (compact) {
    return (
      <div 
        className={`inline-flex items-center space-x-1.5 px-2 py-1 rounded-full text-xs font-medium ${getQualityColorClasses()} ${className}`}
        title={`Connection: ${getQualityLabel()} (${currentRtt ? Math.round(currentRtt) : '--'}ms)`}
      >
        {getSignalBars()}
        <span className="hidden sm:inline">{currentRtt ? `${Math.round(currentRtt)}ms` : '--'}</span>
      </div>
    );
  }

  const warningMessage = getWarningMessage();

  return (
    <div className={`rounded-lg border ${getQualityColorClasses()} ${className}`}>
      {/* Header */}
      <div 
        className="flex items-center justify-between px-3 py-2 cursor-pointer"
        onClick={() => setShowDetails(!showDetails)}
      >
        <div className="flex items-center space-x-2">
          {getQualityIcon()}
          <span className="text-sm font-medium">Connection: {getQualityLabel()}</span>
          {isMonitoring && (
            <span className="text-xs opacity-75">
              ({currentRtt ? `${Math.round(currentRtt)}ms` : 'measuring...'})
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {getSignalBars()}
          {showDetails ? (
            <ChevronUp className="h-4 w-4 opacity-50" />
          ) : (
            <ChevronDown className="h-4 w-4 opacity-50" />
          )}
        </div>
      </div>

      {/* Warning Banner */}
      {warningMessage && (
        <div className="px-3 py-2 text-xs flex items-start space-x-2 border-t border-current/10">
          <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>{warningMessage}</span>
        </div>
      )}

      {/* Detailed Stats */}
      {showDetails && (
        <div className="px-3 py-3 border-t border-current/10 space-y-3">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <div className="opacity-60">Average RTT</div>
              <div className="font-medium flex items-center space-x-1">
                <Activity className="h-3 w-3" />
                <span>{stats.avgRtt.toFixed(1)}ms</span>
              </div>
            </div>
            <div>
              <div className="opacity-60">Jitter</div>
              <div className="font-medium">{stats.jitter.toFixed(1)}ms</div>
            </div>
            <div>
              <div className="opacity-60">Min/Max RTT</div>
              <div className="font-medium">{stats.minRtt.toFixed(0)}/{stats.maxRtt.toFixed(0)}ms</div>
            </div>
            <div>
              <div className="opacity-60">Stability</div>
              <div className="font-medium flex items-center space-x-1">
                <span>{stats.stabilityScore.toFixed(0)}%</span>
                {stats.isStable ? (
                  <span className="text-blue-600 dark:text-blue-400">✓</span>
                ) : (
                  <span className="text-orange-600 dark:text-orange-400">⚠</span>
                )}
              </div>
            </div>
          </div>

          {/* Stability Bar */}
          <div>
            <div className="text-xs opacity-60 mb-1">Connection Stability</div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  stats.stabilityScore >= 70 
                    ? 'bg-blue-500' 
                    : stats.stabilityScore >= 50 
                    ? 'bg-yellow-500' 
                    : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, stats.stabilityScore)}%` }}
              />
            </div>
          </div>

          {/* Samples Info */}
          <div className="flex items-center justify-between text-xs opacity-60">
            <span>Samples: {stats.samplesCount}</span>
            {isMonitoring && (
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <span>Monitoring</span>
              </span>
            )}
          </div>

          {/* Info for engagement context */}
          {(quality === 'poor' || quality === 'critical') && (
            <div className="flex items-start space-x-2 p-2 rounded bg-current/5 text-xs">
              <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium">Engagement Context</div>
                <div className="opacity-75 mt-0.5">
                  Your connection quality is being considered in engagement analysis.
                  Low engagement scores may be adjusted to account for technical difficulties.
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Minimal inline indicator for use in headers/badges
 */
export const ConnectionQualityBadge: React.FC<{
  quality: ConnectionQuality;
  rtt: number | null;
  isMonitoring: boolean;
  className?: string;
}> = ({ quality, rtt, isMonitoring, className = '' }) => {
  const getColorClass = () => {
    if (!isMonitoring) return 'bg-gray-400';
    switch (quality) {
      case 'excellent': return 'bg-blue-500';
      case 'good': return 'bg-blue-400';
      case 'fair': return 'bg-yellow-500';
      case 'poor': return 'bg-orange-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div 
      className={`inline-flex items-center space-x-1.5 text-xs ${className}`}
      title={`Connection: ${quality} (${rtt ? Math.round(rtt) : '--'}ms)`}
    >
      <span className={`w-2 h-2 rounded-full ${getColorClass()} ${isMonitoring ? 'animate-pulse' : ''}`} />
      <span className="text-gray-600 dark:text-gray-400">
        {rtt ? `${Math.round(rtt)}ms` : '--'}
      </span>
    </div>
  );
};

export default ConnectionQualityIndicator;

