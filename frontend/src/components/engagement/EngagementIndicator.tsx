import React from 'react';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface EngagementIndicatorProps {
  engagementLevel: 'high' | 'medium' | 'low';
  engagementScore: number;
  cluster?: string;
  showCluster?: boolean;
}

export const EngagementIndicator: React.FC<EngagementIndicatorProps> = ({
  engagementLevel,
  engagementScore,
  cluster,
  showCluster = false
}) => {
  const getColor = () => {
    switch (engagementLevel) {
      case 'high':
        return 'bg-blue-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getIcon = () => {
    switch (engagementLevel) {
      case 'high':
        return <TrendingUp className="h-4 w-4" />;
      case 'medium':
        return <Minus className="h-4 w-4" />;
      case 'low':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`${getColor()} rounded-full p-1.5 text-white`}>
        {getIcon()}
      </div>
      <div className="flex flex-col">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">
            Engagement: {engagementScore}%
          </span>
          <Badge variant={engagementLevel === 'high' ? 'success' : engagementLevel === 'medium' ? 'warning' : 'danger' as 'success' | 'warning' | 'danger'}>
            {engagementLevel.toUpperCase()}
          </Badge>
        </div>
        {showCluster && cluster && (
          <span className="text-xs text-gray-500">Cluster: {cluster}</span>
        )}
      </div>
    </div>
  );
};

