import React, { useEffect, useState, createContext, useContext } from "react";
import { toast } from "sonner";
import { authService } from "../services/authService";

// ------------------------------
// TYPES
// ------------------------------
interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: "student" | "instructor" | "admin";
  status: number;
  token?: string;       // ⭐ ADDED
  tokenType?: string;   // ⭐ ADDED
}

interface RegisterData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  passwordHint: string;
  role: "student" | "instructor" | "admin";
}

interface AuthContextType {
  user: User | null;
  token: string;
  tokenType: string;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<boolean>;
  resetPassword: (token: string, password: string) => Promise<boolean>;
  activateAccount: (token: string) => Promise<boolean>;
}

// ------------------------------
// CONTEXT
// ------------------------------
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ------------------------------
// PROVIDER
// ------------------------------
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from storage
  const token = localStorage.getItem("access_token") || "";
  const tokenType = localStorage.getItem("token_type") || "Bearer";

  // Load user on page refresh
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        setUser(parsed);
      } catch {
        localStorage.removeItem("user");
      }
    }
    setIsLoading(false);
  }, []);

  // ------------------------------
  // LOGIN
  // ------------------------------
  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await authService.login(email, password);

      if (response.success && response.user && response.access_token) {
        const userWithToken: User = {
          ...response.user,
          token: response.access_token,                   // ⭐ FIX
          tokenType: response.token_type || "Bearer",     // ⭐ FIX
        };

        // Save user + token
        setUser(userWithToken);
        localStorage.setItem("user", JSON.stringify(userWithToken));
        localStorage.setItem("access_token", response.access_token);
        localStorage.setItem("token_type", response.token_type || "Bearer");

        toast.success("Login successful");
        return true;
      }

      toast.error("Invalid credentials");
      return false;
    } catch (err: any) {
      toast.error(err.message || "Login failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // ------------------------------
  // REGISTER
  // ------------------------------
  const register = async (data: RegisterData): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await authService.register({
        firstName: data.firstName,
        lastName: data.lastName,
        email: data.email,
        password: data.password,
        role: data.role,
      });

      if (!response.success) {
        toast.error("Registration failed");
        return false;
      }

      toast.success("Registration successful! Please login.");
      return true;
    } catch (err: any) {
      toast.error(err.message || "Registration failed");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // ------------------------------
  // LOGOUT
  // ------------------------------
  const logout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    setUser(null);
    toast.success("Logged out");
  };

  // ------------------------------
  // OTHERS
  // ------------------------------
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

  // ------------------------------
  // CONTEXT VALUE
  // ------------------------------
  const value: AuthContextType = {
    user,
    token,
    tokenType,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    activateAccount,
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};

// ------------------------------
// HOOK
// ------------------------------
export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
};
