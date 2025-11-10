import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Eye, 
  EyeOff, 
  Lock, 
  Mail, 
  User, 
  Shield, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Brain,
  Zap,
  Users,
  Target,
  Loader2,
  ArrowRight,
  Github,
  Chrome,
  Smartphone
} from 'lucide-react';

const AuthSystem = ({ onLogin, onRegister, isLoading = false, error = null }) => {
  const [activeTab, setActiveTab] = useState('login');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Form states
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const [registerForm, setRegisterForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false
  });

  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    feedback: []
  });

  const [formErrors, setFormErrors] = useState({});

  // Password strength calculation
  useEffect(() => {
    if (registerForm.password) {
      const strength = calculatePasswordStrength(registerForm.password);
      setPasswordStrength(strength);
    } else {
      setPasswordStrength({ score: 0, feedback: [] });
    }
  }, [registerForm.password]);

  const calculatePasswordStrength = (password) => {
    let score = 0;
    const feedback = [];

    if (password.length >= 8) {
      score += 20;
    } else {
      feedback.push('At least 8 characters');
    }

    if (/[a-z]/.test(password)) {
      score += 20;
    } else {
      feedback.push('Include lowercase letters');
    }

    if (/[A-Z]/.test(password)) {
      score += 20;
    } else {
      feedback.push('Include uppercase letters');
    }

    if (/\d/.test(password)) {
      score += 20;
    } else {
      feedback.push('Include numbers');
    }

    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      score += 20;
    } else {
      feedback.push('Include special characters');
    }

    return { score, feedback };
  };

  const getPasswordStrengthColor = (score) => {
    if (score < 40) return 'bg-red-500';
    if (score < 60) return 'bg-orange-500';
    if (score < 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getPasswordStrengthText = (score) => {
    if (score < 40) return 'Weak';
    if (score < 60) return 'Fair';
    if (score < 80) return 'Good';
    return 'Strong';
  };

  // Form validation
  const validateLoginForm = () => {
    const errors = {};
    
    if (!loginForm.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(loginForm.email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!loginForm.password) {
      errors.password = 'Password is required';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateRegisterForm = () => {
    const errors = {};
    
    if (!registerForm.fullName.trim()) {
      errors.fullName = 'Full name is required';
    }
    
    if (!registerForm.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(registerForm.email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!registerForm.password) {
      errors.password = 'Password is required';
    } else if (passwordStrength.score < 60) {
      errors.password = 'Password is too weak';
    }
    
    if (registerForm.password !== registerForm.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    if (!registerForm.acceptTerms) {
      errors.acceptTerms = 'You must accept the terms and conditions';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submissions
  const handleLogin = (e) => {
    e.preventDefault();
    if (validateLoginForm()) {
      // Map email to username field for backend compatibility
      onLogin({
        email: loginForm.email,
        password: loginForm.password
      });
    }
  };

  const handleRegister = (e) => {
    e.preventDefault();
    if (validateRegisterForm()) {
      onRegister({
        name: registerForm.fullName,
        email: registerForm.email,
        password: registerForm.password
      });
    }
  };

  // Handle input changes
  const handleLoginInputChange = (field, value) => {
    setLoginForm(prev => ({ ...prev, [field]: value }));
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleRegisterInputChange = (field, value) => {
    setRegisterForm(prev => ({ ...prev, [field]: value }));
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        
        {/* Left side - Branding and Features */}
        <div className="hidden lg:block space-y-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  MindFlow
                </h1>
                <p className="text-gray-600">Your Personal Productivity Hub</p>
              </div>
            </div>
            
            <p className="text-lg text-gray-700 leading-relaxed">
              Transform your thoughts into actionable insights with intelligent task management, 
              comprehensive stakeholder mapping, and seamless collaboration tools.
            </p>
          </div>

          {/* Feature highlights */}
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Smart Task Planning</h3>
                <p className="text-gray-600 text-sm">
                  AI-powered task categorization with Kanban boards and calendar views
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Users className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Stakeholder Mapping</h3>
                <p className="text-gray-600 text-sm">
                  Interactive network visualization with relationship tracking and insights
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Zap className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Voice & Quick Input</h3>
                <p className="text-gray-600 text-sm">
                  Capture thoughts instantly with voice recognition and smart categorization
                </p>
              </div>
            </div>
          </div>

          {/* Security badges */}
          <div className="flex items-center gap-4 pt-6 border-t border-gray-200">
            <Badge variant="outline" className="flex items-center gap-1">
              <Shield className="h-3 w-3" />
              End-to-end encrypted
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Lock className="h-3 w-3" />
              SOC 2 compliant
            </Badge>
          </div>
        </div>

        {/* Right side - Authentication Forms */}
        <div className="w-full max-w-md mx-auto">
          <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="space-y-1 pb-6">
              <div className="flex items-center justify-center lg:hidden mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                  <Brain className="h-5 w-5 text-white" />
                </div>
              </div>
              <CardTitle className="text-2xl font-bold text-center">
                {activeTab === 'login' ? 'Welcome back' : 'Create your account'}
              </CardTitle>
              <p className="text-gray-600 text-center text-sm">
                {activeTab === 'login' 
                  ? 'Sign in to access your personal productivity hub'
                  : 'Join thousands of users organizing their thoughts'
                }
              </p>
            </CardHeader>

            <CardContent>
              {error && (
                <Alert className="mb-6 border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-700">
                    {error}
                  </AlertDescription>
                </Alert>
              )}

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="login">Sign In</TabsTrigger>
                  <TabsTrigger value="register">Sign Up</TabsTrigger>
                </TabsList>

                {/* Login Form */}
                <TabsContent value="login" className="space-y-4">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="login-email"
                          type="email"
                          placeholder="Enter your email"
                          value={loginForm.email}
                          onChange={(e) => handleLoginInputChange('email', e.target.value)}
                          className={`pl-10 ${formErrors.email ? 'border-red-500' : ''}`}
                        />
                      </div>
                      {formErrors.email && (
                        <p className="text-sm text-red-600">{formErrors.email}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="login-password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Enter your password"
                          value={loginForm.password}
                          onChange={(e) => handleLoginInputChange('password', e.target.value)}
                          className={`pl-10 pr-10 ${formErrors.password ? 'border-red-500' : ''}`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      {formErrors.password && (
                        <p className="text-sm text-red-600">{formErrors.password}</p>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      <label className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={loginForm.rememberMe}
                          onChange={(e) => handleLoginInputChange('rememberMe', e.target.checked)}
                          className="rounded border-gray-300"
                        />
                        <span>Remember me</span>
                      </label>
                      <Button variant="link" className="p-0 h-auto text-sm">
                        Forgot password?
                      </Button>
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Signing in...
                        </>
                      ) : (
                        <>
                          Sign In
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </>
                      )}
                    </Button>
                  </form>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <Separator />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white px-2 text-gray-500">Or continue with</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Button variant="outline" className="w-full">
                      <Github className="mr-2 h-4 w-4" />
                      GitHub
                    </Button>
                    <Button variant="outline" className="w-full">
                      <Chrome className="mr-2 h-4 w-4" />
                      Google
                    </Button>
                  </div>
                </TabsContent>

                {/* Register Form */}
                <TabsContent value="register" className="space-y-4">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name">Full Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-name"
                          type="text"
                          placeholder="Enter your full name"
                          value={registerForm.fullName}
                          onChange={(e) => handleRegisterInputChange('fullName', e.target.value)}
                          className={`pl-10 ${formErrors.fullName ? 'border-red-500' : ''}`}
                        />
                      </div>
                      {formErrors.fullName && (
                        <p className="text-sm text-red-600">{formErrors.fullName}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-email"
                          type="email"
                          placeholder="Enter your email"
                          value={registerForm.email}
                          onChange={(e) => handleRegisterInputChange('email', e.target.value)}
                          className={`pl-10 ${formErrors.email ? 'border-red-500' : ''}`}
                        />
                      </div>
                      {formErrors.email && (
                        <p className="text-sm text-red-600">{formErrors.email}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Create a password"
                          value={registerForm.password}
                          onChange={(e) => handleRegisterInputChange('password', e.target.value)}
                          className={`pl-10 pr-10 ${formErrors.password ? 'border-red-500' : ''}`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      
                      {/* Password strength indicator */}
                      {registerForm.password && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span>Password strength</span>
                            <span className={`font-medium ${
                              passwordStrength.score >= 80 ? 'text-green-600' :
                              passwordStrength.score >= 60 ? 'text-yellow-600' :
                              passwordStrength.score >= 40 ? 'text-orange-600' : 'text-red-600'
                            }`}>
                              {getPasswordStrengthText(passwordStrength.score)}
                            </span>
                          </div>
                          <Progress 
                            value={passwordStrength.score} 
                            className={`h-2 ${getPasswordStrengthColor(passwordStrength.score)}`}
                          />
                          {passwordStrength.feedback.length > 0 && (
                            <div className="text-xs text-gray-600">
                              <p>Improve your password:</p>
                              <ul className="list-disc list-inside space-y-1">
                                {passwordStrength.feedback.map((item, index) => (
                                  <li key={index}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {formErrors.password && (
                        <p className="text-sm text-red-600">{formErrors.password}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-confirm-password">Confirm Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="register-confirm-password"
                          type={showConfirmPassword ? 'text' : 'password'}
                          placeholder="Confirm your password"
                          value={registerForm.confirmPassword}
                          onChange={(e) => handleRegisterInputChange('confirmPassword', e.target.value)}
                          className={`pl-10 pr-10 ${formErrors.confirmPassword ? 'border-red-500' : ''}`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                        {registerForm.confirmPassword && (
                          <div className="absolute right-10 top-3">
                            {registerForm.password === registerForm.confirmPassword ? (
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                          </div>
                        )}
                      </div>
                      {formErrors.confirmPassword && (
                        <p className="text-sm text-red-600">{formErrors.confirmPassword}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <label className="flex items-start space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={registerForm.acceptTerms}
                          onChange={(e) => handleRegisterInputChange('acceptTerms', e.target.checked)}
                          className={`mt-0.5 rounded border-gray-300 ${formErrors.acceptTerms ? 'border-red-500' : ''}`}
                        />
                        <span className="leading-relaxed">
                          I agree to the{' '}
                          <Button variant="link" className="p-0 h-auto text-sm underline">
                            Terms of Service
                          </Button>{' '}
                          and{' '}
                          <Button variant="link" className="p-0 h-auto text-sm underline">
                            Privacy Policy
                          </Button>
                        </span>
                      </label>
                      {formErrors.acceptTerms && (
                        <p className="text-sm text-red-600">{formErrors.acceptTerms}</p>
                      )}
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Creating account...
                        </>
                      ) : (
                        <>
                          Create Account
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </>
                      )}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>

              {/* Mobile app promotion */}
              <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Smartphone className="h-5 w-5 text-blue-600" />
                  <div className="text-sm">
                    <p className="font-medium text-gray-900">Get the mobile app</p>
                    <p className="text-gray-600">Access MindFlow on the go</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="mt-6 text-center text-xs text-gray-500">
            <p>© 2024 MindFlow. All rights reserved.</p>
            <div className="mt-2 space-x-4">
              <Button variant="link" className="p-0 h-auto text-xs">
                Privacy
              </Button>
              <Button variant="link" className="p-0 h-auto text-xs">
                Terms
              </Button>
              <Button variant="link" className="p-0 h-auto text-xs">
                Support
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthSystem;
