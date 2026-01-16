import React from 'react';
interface CardProps {
  children: React.ReactNode;
  className?: string;
}
export const Card: React.FC<CardProps> = ({
  children,
  className = ''
}) => {
  return <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden transition-shadow duration-200 ${className}`}>
      {children}
    </div>;
};
export const CardHeader: React.FC<CardProps> = ({
  children,
  className = ''
}) => {
  return <div className={`px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700 ${className}`}>
      {children}
    </div>;
};
export const CardContent: React.FC<CardProps> = ({
  children,
  className = ''
}) => {
  return <div className={`px-4 py-5 sm:p-6 ${className}`}>{children}</div>;
};
export const CardFooter: React.FC<CardProps> = ({
  children,
  className = ''
}) => {
  return <div className={`px-4 py-4 sm:px-6 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 ${className}`}>
      {children}
    </div>;
};
