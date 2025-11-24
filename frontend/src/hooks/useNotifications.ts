/**
 * useNotifications Hook
 * Manages WebSocket connection for real-time question notifications
 */
import { useState, useEffect, useRef, useCallback } from 'react';

export interface QuestionNotification {
  type: 'question_triggered';
  data: {
    sessionToken: string;
    question: string;
    options: string[];
    timeLimit: number;
    questionUrl: string;
    instructorName: string;
    triggeredAt: string;
  };
  timestamp: string;
}

interface UseNotificationsOptions {
  meetingId: string | null;
  studentId?: string;
  studentName?: string;
  studentEmail?: string;
  autoConnect?: boolean;
}

export function useNotifications(options: UseNotificationsOptions) {
  const { meetingId, studentId, studentName, studentEmail, autoConnect = true } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [currentNotification, setCurrentNotification] = useState<QuestionNotification | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const getWebSocketUrl = useCallback(() => {
    // Get API URL from environment
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    // Convert HTTP(S) to WS(S)
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    const studentIdentifier = studentId || studentEmail || studentName || 'anonymous';
    // Use the new /ws endpoint (not /ws/notifications)
    return `${wsUrl}/ws/${meetingId}/${studentIdentifier}`;
  }, [meetingId, studentId, studentEmail, studentName]);

  const connect = useCallback(() => {
    if (!meetingId || !autoConnect) {
      console.log('⏸️  Notifications: Not connecting (no meetingId or autoConnect=false)');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('✅ Already connected to notifications');
      return;
    }

    try {
      const wsUrl = getWebSocketUrl();
      console.log('🔗 Connecting to notifications:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WS Connected');
        console.log('✅ Connected to notification system');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📬 Received notification:', data);

          // Handle quiz/question notifications
          if (data.type === 'quiz' || data.type === 'question_triggered') {
            const question = data.question || data.data?.question;
            
            if (question) {
              // Show alert for immediate notification
              alert('NEW QUESTION: ' + question);
            }
            
            // Also set the notification state for the popup
            if (data.type === 'question_triggered') {
              setCurrentNotification(data);
            } else if (data.type === 'quiz') {
              // Convert quiz format to question_triggered format
              setCurrentNotification({
                type: 'question_triggered',
                data: {
                  sessionToken: data.sessionToken || '',
                  question: data.question || '',
                  options: data.options || [],
                  timeLimit: data.timeLimit || 30,
                  questionUrl: data.questionUrl || '',
                  instructorName: data.instructorName || 'Instructor',
                  triggeredAt: data.triggeredAt || new Date().toISOString()
                },
                timestamp: data.timestamp || new Date().toISOString()
              });
            }
            
            // Play notification sound
            playNotificationSound();
          } else if (data.type === 'connected') {
            console.log('✅ Notification system ready');
          }
        } catch (error) {
          console.error('❌ Error parsing notification:', error);
        }
      };

      ws.onclose = () => {
        console.log('WS Closed');
        console.log('🔌 Disconnected from notifications');
        setIsConnected(false);
        
        // Attempt to reconnect
        if (autoConnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.onerror = (err) => {
        console.log('WS Error', err);
        console.error('❌ WebSocket error:', err);
        setError('Connection error');
      };

      // Send heartbeat every 30 seconds
      const heartbeatInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);

      // Cleanup heartbeat on unmount
      return () => clearInterval(heartbeatInterval);

    } catch (error) {
      console.error('❌ Failed to connect to notifications:', error);
      setError('Failed to connect');
    }
  }, [meetingId, autoConnect, getWebSocketUrl]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const clearNotification = useCallback(() => {
    setCurrentNotification(null);
  }, []);

  // Auto-connect/disconnect based on options
  useEffect(() => {
    if (autoConnect && meetingId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, meetingId, connect, disconnect]);

  return {
    isConnected,
    currentNotification,
    error,
    connect,
    disconnect,
    clearNotification,
  };
}

// Play notification sound (optional)
function playNotificationSound() {
  try {
    // Create a simple notification beep using Web Audio API
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    // Silent fail - sound is optional
    console.log('Could not play notification sound:', error);
  }
}

