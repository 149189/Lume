'use client';

import { Sparkles } from 'lucide-react';

interface LoginScreenProps {
  onLogin: () => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-md w-full mx-4">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <Sparkles className="w-16 h-16 text-google-blue" strokeWidth={2} />
              <div className="absolute -top-2 -right-2 w-4 h-4 bg-google-yellow rounded-full"></div>
              <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-google-red rounded-full"></div>
              <div className="absolute top-1/2 -right-3 w-3 h-3 bg-google-green rounded-full"></div>
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-2">
            <span className="text-google-blue">L</span>
            <span className="text-google-red">U</span>
            <span className="text-google-yellow">M</span>
            <span className="text-google-green">E</span>
          </h1>
          <p className="text-gray-600 text-lg">Your AI Productivity Assistant</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-2 text-center">
            Welcome to LUME
          </h2>
          <p className="text-gray-600 text-center mb-6">
            Seamlessly manage your Gmail, Calendar, Tasks, and Keep with AI
          </p>

          <button
            onClick={onLogin}
            className="w-full bg-white border-2 border-gray-300 text-gray-700 font-medium py-3 px-6 rounded-lg hover:bg-gray-50 hover:border-google-blue transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm hover:shadow-md"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span>Sign in with Google</span>
          </button>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Features:</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-google-blue rounded-full mr-2"></span>
                Smart email management with Gmail
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-google-red rounded-full mr-2"></span>
                Calendar event scheduling
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-google-yellow rounded-full mr-2"></span>
                Task tracking and reminders
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-google-green rounded-full mr-2"></span>
                Note-taking with Google Keep
              </li>
            </ul>
          </div>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          By signing in, you agree to grant necessary permissions for LUME to access your Google services
        </p>
      </div>
    </div>
  );
}
