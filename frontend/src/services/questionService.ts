// Question service for handling question-related API calls

export interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  tags: string[];
  timeLimit?: number;
  createdAt?: string;
}

export interface CreateQuestionData {
  question: string;
  options: string[];
  correctAnswer: number;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  tags?: string[];
  timeLimit?: number;
}

// ✔ Correct API root — no slash, no /api suffix
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth token and user role from localStorage
const getAuthToken = (): string => {
  try {
    const user = localStorage.getItem('user');
    if (user) {
      const userData = JSON.parse(user);
      return userData.token || 'mock-token';
    }
  } catch (error) {
    console.error('Error getting auth token:', error);
  }
  return 'mock-token';
};

const getUserRole = (): string => {
  try {
    const user = localStorage.getItem('user');
    if (user) {
      const userData = JSON.parse(user);
      return userData.role || 'student';
    }
  } catch (error) {
    console.error('Error getting user role:', error);
  }
  return 'student';
};

export const questionService = {
  // Create a new question
  async createQuestion(questionData: CreateQuestionData): Promise<Question> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/questions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
          'x-user-role': getUserRole(),
        },
        body: JSON.stringify(questionData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        let errorMessage = `Failed to create question: ${response.status}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorJson.message || errorMessage;
        } catch {
          // If errorText is not JSON, use it as is
          if (errorText) {
            errorMessage = errorText;
          }
        }
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating question:', error);
      throw error;
    }
  },

  // Get all questions
  async getAllQuestions(): Promise<Question[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/questions/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
          'x-user-role': getUserRole(),
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to get questions: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting questions:', error);
      // Return empty array on error instead of throwing
      return [];
    }
  },

  // Get a question by ID
  async getQuestionById(questionId: string): Promise<Question> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/questions/${questionId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
          'x-user-role': getUserRole(),
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to get question: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting question:', error);
      throw error;
    }
  },

  // Update a question
  async updateQuestion(questionId: string, questionData: CreateQuestionData): Promise<Question> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/questions/${questionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
          'x-user-role': getUserRole(),
        },
        body: JSON.stringify(questionData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to update question: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating question:', error);
      throw error;
    }
  },

  // Delete a question
  async deleteQuestion(questionId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/questions/${questionId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
          'x-user-role': getUserRole(),
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText);
        throw new Error(`Failed to delete question: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting question:', error);
      throw error;
    }
  },
};

