// Session service communicating with BACKEND API
export interface Session {
  id: string;
  title: string;
  course: string;
  courseCode: string;
  instructor: string;
  date: string;
  time: string;
  duration: string;
  status: 'live' | 'upcoming' | 'completed';
  participants?: number;
  expectedParticipants?: number;
  engagement?: number;
  zoomMeetingId?: string;
  join_url?: string;
  start_url?: string;
  recordingAvailable?: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_URL;

export const sessionService = {
  async getAllSessions(): Promise<Session[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sessions`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
        },
      });

      if (!res.ok) {
        console.error("Failed to fetch sessions:", await res.text());
        return [];
      }

      return await res.json();
    } catch (err) {
      console.error("Session fetch error:", err);
      return [];
    }
  },

  async getSession(id: string): Promise<Session | null> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${id}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
      },
    });

    if (!res.ok) return null;

    return await res.json();
  },

  async createSession(payload: {
    title: string;
    course: string;
    courseCode: string;
    date: string;          // yyyy-mm-dd
    time: string;          // HH:MM (24hr)
    durationMinutes: number;
    timezone?: string;
  }): Promise<Session> {
    const res = await fetch(`${API_BASE_URL}/api/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Failed to create session: ${txt}`);
    }

    return await res.json();
  },
};
