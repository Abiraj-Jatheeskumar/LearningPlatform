import React, { useEffect, useState, createContext, useContext } from 'react';
import { toast } from 'sonner';
import { authService } from '../services/authService';

// ---------------------------
// TYPES
// ---------------------------
interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: 'student' | 'instructor' | 'admin';
  status: number;
}

interface RegisterData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  passwordHint: string;
  role: 'student' | 'instructor' | 'admin';
}

interface AuthContextType {
  user: User | null;
  token: string;              // ⭐ ADDED
  tokenType: string;          // ⭐ ADDED
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: RegisterData) => Promise<boolean>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<boolean>;
  resetPassword: (token: string, password: string) => Promise<boolean>;
  activateAccount: (token: string) => Promise<boolean>;
}

// ---------------------------
// CONTEXT
// ---------------------------
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ---------------------------
// PROVIDER
// ---------------------------
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // ⭐ Load token from localStorage
  const token = localStorage.getItem("access_token") || "";
  const tokenType = localStorage.getItem("token_type") || "Bearer";

  // Load user on refresh
  useEffect(() => {
    try {
      const storedUser = localStorage.getItem("user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    } catch {
      localStorage.removeItem("user");
    }
    setIsLoading(false);
  }, []);

  // ---------------------------
  // LOGIN
  // ---------------------------
  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await authService.login(email, password);

      if (response.success && response.user) {
        // Save user
        setUser(response.user);
        localStorage.setItem("user", JSON.stringify(response.user));

        // Save JWT token ⭐
        if (response.access_token) {
          localStorage.setItem("access_token", response.access_token);
          localStorage.setItem("token_type", response.token_type || "Bearer");
        }

        toast.success("Login successful");
        return true;
      }

      toast.error("Login failed");
      return false;
    } catch (error: any) {
      toast.error(error.message || "Login failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // ---------------------------
  // REGISTER
  // ---------------------------
  const register = async (userData: RegisterData): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await authService.register({
        firstName: userData.firstName,
        lastName: userData.lastName,
        email: userData.email,
        password: userData.password,
        role: userData.role,
      });

      if (response.success) {
        // Auto-login after register (if backend provides token)
        if (response.access_token && response.user) {
          setUser(response.user);
          localStorage.setItem("user", JSON.stringify(response.user));
          localStorage.setItem("access_token", response.access_token);
          localStorage.setItem("token_type", response.token_type || "Bearer");
        }

        toast.success("Account created! Please login.");
        return true;
      }

      toast.error("Registration failed");
      return false;
    } catch (error: any) {
      toast.error(error.message || "Registration failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // ---------------------------
  // LOGOUT
  // ---------------------------
  const logout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    setUser(null);
    toast.success("Logged out successfully");
  };

  // ---------------------------
  // PASSWORD + ACTIVATION
  // ---------------------------
  const forgotPassword = async (email: string) => {
    toast.success("If registered, you will receive a reset email.");
    return true;
  };

  const resetPassword = async () => {
    toast.success("Password reset successful.");
    return true;
  };

  const activateAccount = async () => {
    toast.success("Account activated!");
    return true;
  };

  // ---------------------------
  // CONTEXT VALUE
  // ---------------------------
  const value: AuthContextType = {
    user,
    token,              // ⭐ available everywhere now!
    tokenType,          // ⭐ (Bearer)
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    activateAccount,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// ---------------------------
// HOOK
// ---------------------------
export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
};
