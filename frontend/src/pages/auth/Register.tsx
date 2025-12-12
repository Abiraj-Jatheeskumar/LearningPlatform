import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { AuthLayout } from '../../components/auth/AuthLayout';
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, Loader2, GraduationCap, BookOpen, CheckCircle2 } from 'lucide-react';

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  passwordHint: string;
  role: 'student' | 'instructor' | 'admin';
}

interface FormErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  role?: string;
}

const passwordRequirements = [
  { regex: /.{6,}/, text: 'At least 6 characters' },
  { regex: /[a-z]/, text: 'One lowercase letter' },
  { regex: /[A-Z]/, text: 'One uppercase letter' },
  { regex: /\d/, text: 'One number' },
];

export const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    passwordHint: '',
    role: 'student'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [step, setStep] = useState(1);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    if (errors[name as keyof FormErrors]) {
      setErrors({ ...errors, [name]: undefined });
    }
  };

  const validateStep1 = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    } else if (formData.firstName.trim().length < 2) {
      newErrors.firstName = 'First name must be at least 2 characters';
    }
    
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    } else if (formData.lastName.trim().length < 2) {
      newErrors.lastName = 'Last name must be at least 2 characters';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateStep2()) {
      return;
    }

    setIsLoading(true);
    setErrors({});
    
    const success = await register(formData);
    
    if (success) {
      navigate('/login');
    }
    
    setIsLoading(false);
  };

  const getPasswordStrength = () => {
    const passed = passwordRequirements.filter(req => req.regex.test(formData.password)).length;
    if (passed === 0) return { width: '0%', color: 'bg-gray-200', text: '' };
    if (passed === 1) return { width: '25%', color: 'bg-red-500', text: 'Weak' };
    if (passed === 2) return { width: '50%', color: 'bg-orange-500', text: 'Fair' };
    if (passed === 3) return { width: '75%', color: 'bg-yellow-500', text: 'Good' };
    return { width: '100%', color: 'bg-green-500', text: 'Strong' };
  };

  const passwordStrength = getPasswordStrength();

  return (
    <AuthLayout 
      title={step === 1 ? "Create your account" : "Secure your account"}
      subtitle={step === 1 ? "Start your learning journey today" : "Set a strong password to protect your account"}
    >
      {/* Progress Steps */}
      <div className="flex items-center gap-3 mb-8">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full font-semibold text-sm transition-all duration-300 ${
          step >= 1 ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
        }`}>
          {step > 1 ? <CheckCircle2 className="w-5 h-5" /> : '1'}
        </div>
        <div className={`flex-1 h-1 rounded-full transition-all duration-300 ${
          step > 1 ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
        }`} />
        <div className={`flex items-center justify-center w-8 h-8 rounded-full font-semibold text-sm transition-all duration-300 ${
          step >= 2 ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
        }`}>
          2
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Personal Info */}
        <div className={`space-y-5 ${step === 1 ? 'block' : 'hidden'}`}>
          {/* Name Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                First name
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className={`h-5 w-5 transition-colors duration-200 ${
                    errors.firstName ? 'text-red-400' : 'text-gray-400 group-focus-within:text-indigo-500'
                  }`} />
                </div>
                <input
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className={`
                    block w-full pl-12 pr-4 py-3.5 rounded-xl border-2 transition-all duration-200
                    bg-white dark:bg-gray-800 
                    text-gray-900 dark:text-white
                    placeholder-gray-400 dark:placeholder-gray-500
                    focus:outline-none focus:ring-0
                    ${errors.firstName 
                      ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                      : 'border-gray-200 dark:border-gray-700 focus:border-indigo-500 dark:focus:border-indigo-400'
                    }
                  `}
                  placeholder="John"
                />
              </div>
              {errors.firstName && (
                <p className="text-sm text-red-500 animate-shake">{errors.firstName}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Last name
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className={`h-5 w-5 transition-colors duration-200 ${
                    errors.lastName ? 'text-red-400' : 'text-gray-400 group-focus-within:text-indigo-500'
                  }`} />
                </div>
                <input
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className={`
                    block w-full pl-12 pr-4 py-3.5 rounded-xl border-2 transition-all duration-200
                    bg-white dark:bg-gray-800 
                    text-gray-900 dark:text-white
                    placeholder-gray-400 dark:placeholder-gray-500
                    focus:outline-none focus:ring-0
                    ${errors.lastName 
                      ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                      : 'border-gray-200 dark:border-gray-700 focus:border-indigo-500 dark:focus:border-indigo-400'
                    }
                  `}
                  placeholder="Doe"
                />
              </div>
              {errors.lastName && (
                <p className="text-sm text-red-500 animate-shake">{errors.lastName}</p>
              )}
            </div>
          </div>

          {/* Email */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Email address
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Mail className={`h-5 w-5 transition-colors duration-200 ${
                  errors.email ? 'text-red-400' : 'text-gray-400 group-focus-within:text-indigo-500'
                }`} />
              </div>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`
                  block w-full pl-12 pr-4 py-3.5 rounded-xl border-2 transition-all duration-200
                  bg-white dark:bg-gray-800 
                  text-gray-900 dark:text-white
                  placeholder-gray-400 dark:placeholder-gray-500
                  focus:outline-none focus:ring-0
                  ${errors.email 
                    ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                    : 'border-gray-200 dark:border-gray-700 focus:border-indigo-500 dark:focus:border-indigo-400'
                  }
                `}
                placeholder="you@example.com"
              />
            </div>
            {errors.email && (
              <p className="text-sm text-red-500 animate-shake">{errors.email}</p>
            )}
          </div>

          {/* Role Selection */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              I am a
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, role: 'student' })}
                className={`
                  flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all duration-200
                  ${formData.role === 'student'
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                  formData.role === 'student' 
                    ? 'bg-indigo-100 dark:bg-indigo-900/40' 
                    : 'bg-gray-100 dark:bg-gray-800'
                }`}>
                  <GraduationCap className={`w-6 h-6 ${
                    formData.role === 'student' ? 'text-indigo-600' : 'text-gray-500'
                  }`} />
                </div>
                <span className={`font-medium ${
                  formData.role === 'student' 
                    ? 'text-indigo-600 dark:text-indigo-400' 
                    : 'text-gray-700 dark:text-gray-300'
                }`}>
                  Student
                </span>
              </button>

              <button
                type="button"
                onClick={() => setFormData({ ...formData, role: 'instructor' })}
                className={`
                  flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all duration-200
                  ${formData.role === 'instructor'
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                  formData.role === 'instructor' 
                    ? 'bg-indigo-100 dark:bg-indigo-900/40' 
                    : 'bg-gray-100 dark:bg-gray-800'
                }`}>
                  <BookOpen className={`w-6 h-6 ${
                    formData.role === 'instructor' ? 'text-indigo-600' : 'text-gray-500'
                  }`} />
                </div>
                <span className={`font-medium ${
                  formData.role === 'instructor' 
                    ? 'text-indigo-600 dark:text-indigo-400' 
                    : 'text-gray-700 dark:text-gray-300'
                }`}>
                  Instructor
                </span>
              </button>
            </div>
          </div>

          {/* Next Button */}
          <button
            type="button"
            onClick={handleNextStep}
            className="
              w-full py-4 px-6 rounded-xl font-semibold text-white
              bg-gradient-to-r from-indigo-600 to-purple-600 
              hover:from-indigo-700 hover:to-purple-700
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
              transform hover:scale-[1.02] active:scale-[0.98]
              transition-all duration-200
              shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30
              flex items-center justify-center gap-2
              group
            "
          >
            Continue
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        {/* Step 2: Password */}
        <div className={`space-y-5 ${step === 2 ? 'block' : 'hidden'}`}>
          {/* Password */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Password
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Lock className={`h-5 w-5 transition-colors duration-200 ${
                  errors.password ? 'text-red-400' : 'text-gray-400 group-focus-within:text-indigo-500'
                }`} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`
                  block w-full pl-12 pr-12 py-3.5 rounded-xl border-2 transition-all duration-200
                  bg-white dark:bg-gray-800 
                  text-gray-900 dark:text-white
                  placeholder-gray-400 dark:placeholder-gray-500
                  focus:outline-none focus:ring-0
                  ${errors.password 
                    ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                    : 'border-gray-200 dark:border-gray-700 focus:border-indigo-500 dark:focus:border-indigo-400'
                  }
                `}
                placeholder="Create a password"
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
            {formData.password && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${passwordStrength.color} transition-all duration-300`}
                      style={{ width: passwordStrength.width }}
                    />
                  </div>
                  <span className={`text-xs font-medium ${
                    passwordStrength.color === 'bg-green-500' ? 'text-green-600' :
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
                        req.regex.test(formData.password) 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-gray-400'
                      }`}
                    >
                      <CheckCircle2 className={`w-3.5 h-3.5 ${
                        req.regex.test(formData.password) ? 'opacity-100' : 'opacity-30'
                      }`} />
                      {req.text}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {errors.password && (
              <p className="text-sm text-red-500 animate-shake">{errors.password}</p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Confirm password
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Lock className={`h-5 w-5 transition-colors duration-200 ${
                  errors.confirmPassword ? 'text-red-400' : 'text-gray-400 group-focus-within:text-indigo-500'
                }`} />
              </div>
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`
                  block w-full pl-12 pr-12 py-3.5 rounded-xl border-2 transition-all duration-200
                  bg-white dark:bg-gray-800 
                  text-gray-900 dark:text-white
                  placeholder-gray-400 dark:placeholder-gray-500
                  focus:outline-none focus:ring-0
                  ${errors.confirmPassword 
                    ? 'border-red-300 dark:border-red-600 focus:border-red-500' 
                    : 'border-gray-200 dark:border-gray-700 focus:border-indigo-500 dark:focus:border-indigo-400'
                  }
                `}
                placeholder="Confirm your password"
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
            {formData.confirmPassword && formData.password === formData.confirmPassword && (
              <p className="text-sm text-green-600 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" />
                Passwords match
              </p>
            )}
            {errors.confirmPassword && (
              <p className="text-sm text-red-500 animate-shake">{errors.confirmPassword}</p>
            )}
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="
                flex-1 py-4 px-6 rounded-xl font-semibold
                text-gray-700 dark:text-gray-200
                bg-gray-100 dark:bg-gray-800
                hover:bg-gray-200 dark:hover:bg-gray-700
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500
                transition-all duration-200
              "
            >
              Back
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="
                relative flex-1 py-4 px-6 rounded-xl font-semibold text-white
                bg-gradient-to-r from-indigo-600 to-purple-600 
                hover:from-indigo-700 hover:to-purple-700
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                disabled:opacity-70 disabled:cursor-not-allowed
                transform hover:scale-[1.02] active:scale-[0.98]
                transition-all duration-200
                shadow-lg shadow-indigo-500/25
                group overflow-hidden
              "
            >
              <span className={`flex items-center justify-center gap-2 ${isLoading ? 'opacity-0' : ''}`}>
                Create account
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200 dark:border-gray-700" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400">
            Already have an account?
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
          border-2 border-gray-200 dark:border-gray-700
          hover:border-indigo-500 dark:hover:border-indigo-400
          hover:text-indigo-600 dark:hover:text-indigo-400
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
          transform hover:scale-[1.02] active:scale-[0.98]
          transition-all duration-200
          group
        "
      >
        Sign in to your account
        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
      </Link>
    </AuthLayout>
  );
};
