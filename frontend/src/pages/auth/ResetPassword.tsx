import React, { useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { AuthLayout } from '../../components/auth/AuthLayout';
import { authService } from '../../services/authService';
import { Lock, Eye, EyeOff, ArrowRight, Loader2, CheckCircle2, Shield } from 'lucide-react';
import { toast } from 'sonner';

const passwordRequirements = [
  { regex: /.{6,}/, text: 'At least 6 characters' },
  { regex: /[a-z]/, text: 'One lowercase letter' },
  { regex: /[A-Z]/, text: 'One uppercase letter' },
  { regex: /\d/, text: 'One number' },
];

export const ResetPassword = () => {
  const navigate = useNavigate();
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ password?: string; confirmPassword?: string }>({});

  const getPasswordStrength = () => {
    const passed = passwordRequirements.filter(req => req.regex.test(password)).length;
    if (passed === 0) return { width: '0%', color: 'bg-gray-200', text: '' };
    if (passed === 1) return { width: '25%', color: 'bg-red-500', text: 'Weak' };
    if (passed === 2) return { width: '50%', color: 'bg-orange-500', text: 'Fair' };
    if (passed === 3) return { width: '75%', color: 'bg-yellow-500', text: 'Good' };
    return { width: '100%', color: 'bg-blue-500', text: 'Strong' };
  };

  const validateForm = () => {
    const newErrors: { password?: string; confirmPassword?: string } = {};

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      await authService.resetPassword(token || '', password);
      toast.success('Password reset successfully!');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.message || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength = getPasswordStrength();

  return (
    <AuthLayout 
      title="Create new password" 
      subtitle="Enter a strong password to secure your account"
    >
      {/* Security Badge */}
      <div className="flex items-center gap-2 p-3 mb-6 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
        <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <span className="text-sm text-blue-800 dark:text-blue-300">
          Secure password reset - your connection is encrypted
        </span>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        {/* New Password Field */}
        <div className="space-y-2">
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            New password
          </label>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className={`h-5 w-5 transition-colors duration-200 ${
                errors.password ? 'text-red-400' : 'text-gray-400 group-focus-within:text-blue-500'
              }`} />
            </div>
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errors.password) setErrors({ ...errors, password: undefined });
              }}
              className={`
                block w-full pl-12 pr-12 py-3.5 rounded-xl border-2 transition-all duration-200
                bg-white dark:bg-gray-800 
                text-gray-900 dark:text-white
                placeholder-gray-400 dark:placeholder-gray-500
                focus:outline-none focus:ring-0
                ${errors.password 
                  ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                  : 'border-gray-200 dark:border-gray-700 focus:border-blue-500 dark:focus:border-blue-400'
                }
              `}
              placeholder="Create a new password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-4 flex items-center"
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600 transition-colors" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600 transition-colors" />
              )}
            </button>
          </div>

          {/* Password Strength */}
          {password && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${passwordStrength.color} transition-all duration-300`}
                    style={{ width: passwordStrength.width }}
                  />
                </div>
                <span className={`text-xs font-medium ${
                  passwordStrength.color === 'bg-blue-500' ? 'text-blue-600' :
                  passwordStrength.color === 'bg-yellow-500' ? 'text-yellow-600' :
                  passwordStrength.color === 'bg-orange-500' ? 'text-orange-600' :
                  'text-red-600'
                }`}>
                  {passwordStrength.text}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                {passwordRequirements.map((req) => (
                  <div 
                    key={req.text}
                    className={`flex items-center gap-2 text-xs ${
                      req.regex.test(password) 
                        ? 'text-blue-600 dark:text-blue-400' 
                        : 'text-gray-400'
                    }`}
                  >
                    <CheckCircle2 className={`w-3.5 h-3.5 ${
                      req.regex.test(password) ? 'opacity-100' : 'opacity-30'
                    }`} />
                    {req.text}
                  </div>
                ))}
              </div>
            </div>
          )}

          {errors.password && (
            <p className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1 animate-shake">
              <span className="inline-block w-1 h-1 bg-red-500 rounded-full" />
              {errors.password}
            </p>
          )}
        </div>

        {/* Confirm Password Field */}
        <div className="space-y-2">
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Confirm new password
          </label>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className={`h-5 w-5 transition-colors duration-200 ${
                errors.confirmPassword ? 'text-red-400' : 'text-gray-400 group-focus-within:text-blue-500'
              }`} />
            </div>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              required
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: undefined });
              }}
              className={`
                block w-full pl-12 pr-12 py-3.5 rounded-xl border-2 transition-all duration-200
                bg-white dark:bg-gray-800 
                text-gray-900 dark:text-white
                placeholder-gray-400 dark:placeholder-gray-500
                focus:outline-none focus:ring-0
                ${errors.confirmPassword 
                  ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                  : 'border-gray-200 dark:border-gray-700 focus:border-blue-500 dark:focus:border-blue-400'
                }
              `}
              placeholder="Confirm your new password"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute inset-y-0 right-0 pr-4 flex items-center"
            >
              {showConfirmPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600 transition-colors" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600 transition-colors" />
              )}
            </button>
          </div>
          {confirmPassword && password === confirmPassword && (
            <p className="text-sm text-blue-600 flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" />
              Passwords match
            </p>
          )}
          {errors.confirmPassword && (
            <p className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1 animate-shake">
              <span className="inline-block w-1 h-1 bg-red-500 rounded-full" />
              {errors.confirmPassword}
            </p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="
            relative w-full py-4 px-6 rounded-xl font-semibold text-white
            bg-gradient-to-r from-blue-500 via-blue-600 to-blue-600 
            hover:from-blue-600 hover:via-blue-700 hover:to-blue-700
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            disabled:opacity-70 disabled:cursor-not-allowed
            transform hover:scale-[1.02] active:scale-[0.98]
            transition-all duration-200
            shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40
            group overflow-hidden
          "
        >
          <span className={`flex items-center justify-center gap-2 ${isLoading ? 'opacity-0' : ''}`}>
            Reset password
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </span>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200 dark:border-gray-700" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400">
            Remember your password?
          </span>
        </div>
      </div>

      {/* Login Link */}
      <Link
        to="/login"
        className="
          flex items-center justify-center gap-2 w-full py-4 px-6 rounded-xl
          font-semibold text-gray-700 dark:text-gray-200
          bg-white dark:bg-gray-800
          border-2 border-blue-200 dark:border-blue-800
          hover:border-blue-500 dark:hover:border-blue-400
          hover:text-blue-600 dark:hover:text-blue-400
          hover:bg-blue-50 dark:hover:bg-blue-900/20
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
          transform hover:scale-[1.02] active:scale-[0.98]
          transition-all duration-200
          group
        "
      >
        Back to sign in
        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
      </Link>
    </AuthLayout>
  );
};
