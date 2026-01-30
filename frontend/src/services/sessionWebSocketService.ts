/**
 * Shared WebSocket Service for Session Connections
 * Ensures consistent WebSocket connection management across all components
 */

let globalSessionWs: WebSocket | null = null;
let globalConnectedSessionId: string | null = null;

export interface JoinSessionOptions {
  sessionKey: string;
  studentId: string;
  studentName: string;
  studentEmail: string;
  onOpen?: () => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

/**
 * Get WebSocket base URL consistently across all components
 */
export function getWebSocketBaseUrl(): string {
  // Priority: VITE_WS_URL > VITE_API_URL (converted) > default
  const wsUrl = import.meta.env.VITE_WS_URL;
  if (wsUrl) {
    return wsUrl;
  }
  
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3001';
  // Convert http:// to ws:// and https:// to wss://
  return apiUrl.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
}

/**
 * Join a session - closes any existing connection first
 */
export function joinSession(options: JoinSessionOptions): WebSocket | null {
  const { sessionKey, studentId, studentName, studentEmail, onOpen, onMessage, onClose, onError } = options;
  
  // Close any existing connection first
  if (globalSessionWs) {
    console.log('🔌 [SessionWS] Closing existing WebSocket connection');
    globalSessionWs.close();
    globalSessionWs = null;
  }
  
  // Build WebSocket URL
  const wsBase = getWebSocketBaseUrl();
  const encodedName = encodeURIComponent(studentName);
  const encodedEmail = encodeURIComponent(studentEmail);
  const sessionWsUrl = `${wsBase}/ws/session/${sessionKey}/${studentId}?student_name=${encodedName}&student_email=${encodedEmail}`;
  
  console.log(`🔗 [SessionWS] Connecting to session WebSocket: ${sessionWsUrl}`);
  
  try {
    const ws = new WebSocket(sessionWsUrl);
    
    ws.onopen = () => {
      console.log(`✅ [SessionWS] Connected to session ${sessionKey} WebSocket`);
      globalSessionWs = ws;
      globalConnectedSessionId = sessionKey;
      localStorage.setItem('connectedSessionId', sessionKey);
      
      if (onOpen) {
        onOpen();
      }
    };
    
    ws.onmessage = (event) => {
      if (onMessage) {
        onMessage(event);
      }
    };
    
    ws.onclose = () => {
      console.log(`🔌 [SessionWS] Session ${sessionKey} WebSocket closed`);
      
      if (globalSessionWs === ws) {
        globalSessionWs = null;
        if (globalConnectedSessionId === sessionKey) {
          globalConnectedSessionId = null;
          localStorage.removeItem('connectedSessionId');
        }
      }
      
      if (onClose) {
        onClose();
      }
    };
    
    ws.onerror = (error) => {
      console.error(`❌ [SessionWS] WebSocket error:`, error);
      if (onError) {
        onError(error);
      }
    };
    
    return ws;
  } catch (error) {
    console.error('❌ [SessionWS] Failed to create WebSocket:', error);
    return null;
  }
}

/**
 * Leave current session
 */
export function leaveSession(): void {
  if (globalSessionWs) {
    console.log('🔌 [SessionWS] Leaving session');
    globalSessionWs.close();
    globalSessionWs = null;
    globalConnectedSessionId = null;
    localStorage.removeItem('connectedSessionId');
  }
}

/**
 * Get current connected session ID
 */
export function getConnectedSessionId(): string | null {
  return globalConnectedSessionId || localStorage.getItem('connectedSessionId');
}

/**
 * Check if connected to a specific session
 */
export function isConnectedToSession(sessionKey: string): boolean {
  const connectedId = getConnectedSessionId();
  return connectedId === sessionKey;
}

/**
 * Get current WebSocket connection
 */
export function getCurrentWebSocket(): WebSocket | null {
  return globalSessionWs;
}

