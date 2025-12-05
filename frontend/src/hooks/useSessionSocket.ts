/**
 * useSessionSocket Hook
 * Manages Socket.IO connection for session-based quiz delivery
 * 🎯 Only students who join a session will receive quiz questions
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

export interface QuizNotification {
  type: 'quiz' | 'NEW_QUESTION';
  sessionId?: string;
  session_id?: string;
  questionId?: string;
  question_id?: string;
  question: string;
  options: string[];
  timeLimit?: number;
  time_limit?: number;
  triggeredAt?: string;
  triggered_at?: string;
}

interface UseSessionSocketOptions {
  sessionId: string | null;
  studentId?: string;
  studentName?: string;
  studentEmail?: string;
  autoConnect?: boolean;
  onQuizReceived?: (quiz: QuizNotification) => void;
}

export function useSessionSocket(options: UseSessionSocketOptions) {
  const { 
    sessionId, 
    studentId, 
    studentName, 
    studentEmail, 
    autoConnect = true,
    onQuizReceived 
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isJoined, setIsJoined] = useState(false);
  const [participantCount, setParticipantCount] = useState(0);
  const [currentQuiz, setCurrentQuiz] = useState<QuizNotification | null>(null);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<Socket | null>(null);

  const getSocketUrl = useCallback(() => {
    // Use the realtime backend URL (Flask-SocketIO)
    const realtimeUrl = import.meta.env.VITE_REALTIME_URL || 
                        import.meta.env.VITE_SOCKETIO_URL || 
                        'http://localhost:5000';
    return realtimeUrl;
  }, []);

  const connect = useCallback(() => {
    if (!sessionId || !studentId || !autoConnect) {
      console.log('⏸️ SessionSocket: Not connecting (missing sessionId or studentId)');
      return;
    }

    if (socketRef.current?.connected) {
      console.log('✅ Already connected to session socket');
      return;
    }

    try {
      const socketUrl = getSocketUrl();
      console.log('🔗 Connecting to session socket:', socketUrl);

      const socket = io(socketUrl, {
        transports: ['websocket', 'polling'],
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      socketRef.current = socket;

      socket.on('connect', () => {
        console.log('✅ Socket.IO connected:', socket.id);
        setIsConnected(true);
        setError(null);

        // 🎯 Join the session room immediately after connecting
        socket.emit('join_session', {
          session_id: sessionId,
          sessionId: sessionId,
          student_id: studentId,
          studentId: studentId,
          name: studentName,
          studentName: studentName,
          email: studentEmail,
          studentEmail: studentEmail,
        });
      });

      // Handle session join confirmation
      socket.on('session_joined', (data) => {
        console.log('✅ Joined session room:', data);
        setIsJoined(true);
        setParticipantCount(data.participant_count || data.participantCount || 0);
      });

      // 🎯 Handle quiz questions (only received if in session room)
      socket.on('NEW_QUESTION', (data: QuizNotification) => {
        console.log('📬 Received quiz question:', data);
        setCurrentQuiz(data);
        
        if (onQuizReceived) {
          onQuizReceived(data);
        }

        // Play notification sound
        playNotificationSound();
      });

      // Also listen for 'quiz' event type
      socket.on('quiz', (data: QuizNotification) => {
        console.log('📬 Received quiz (quiz event):', data);
        setCurrentQuiz({ ...data, type: 'quiz' });
        
        if (onQuizReceived) {
          onQuizReceived({ ...data, type: 'quiz' });
        }

        playNotificationSound();
      });

      // Handle student joined notifications (for instructor)
      socket.on('student_joined_session', (data) => {
        console.log('👤 Student joined session:', data);
        setParticipantCount(data.participant_count || data.participantCount || 0);
      });

      // Handle errors
      socket.on('error', (data) => {
        console.error('❌ Socket error:', data);
        setError(data.message || 'Connection error');
      });

      socket.on('disconnect', () => {
        console.log('🔌 Socket.IO disconnected');
        setIsConnected(false);
        setIsJoined(false);
      });

      socket.on('connect_error', (err) => {
        console.error('❌ Connection error:', err);
        setError('Failed to connect to session');
      });

    } catch (error) {
      console.error('❌ Failed to connect to session socket:', error);
      setError('Failed to connect');
    }
  }, [sessionId, studentId, studentName, studentEmail, autoConnect, getSocketUrl, onQuizReceived]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      // Leave session before disconnecting
      if (sessionId && studentId) {
        socketRef.current.emit('leave_session', {
          session_id: sessionId,
          student_id: studentId,
        });
      }

      socketRef.current.disconnect();
      socketRef.current = null;
    }

    setIsConnected(false);
    setIsJoined(false);
  }, [sessionId, studentId]);

  const clearQuiz = useCallback(() => {
    setCurrentQuiz(null);
  }, []);

  // Auto-connect when options change
  useEffect(() => {
    if (autoConnect && sessionId && studentId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, sessionId, studentId, connect, disconnect]);

  return {
    isConnected,
    isJoined,
    participantCount,
    currentQuiz,
    error,
    connect,
    disconnect,
    clearQuiz,
    socket: socketRef.current,
  };
}

// Play notification sound
function playNotificationSound() {
  try {
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
    console.log('Could not play notification sound:', error);
  }
}

export default useSessionSocket;

