/**
 * Lume AI Productivity Agent - Frontend API Client
 * Comprehensive TypeScript API service for Next.js frontend communication with FastAPI backend
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

// Node.js process type declaration for environments
declare const process: {
  env: {
    NEXT_PUBLIC_API_BASE_URL?: string;
    [key: string]: string | undefined;
  };
};

// Custom HTTP client interfaces
interface HttpRequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  url: string;
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  metadata?: {
    startTime: number;
  };
  _retry?: boolean;
}

interface HttpResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: HttpRequestConfig;
}

interface HttpError extends Error {
  response?: {
    data?: any;
    status: number;
    statusText: string;
  };
  request?: any;
  config?: HttpRequestConfig;
}

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * Generic API Response wrapper
 */
export interface ApiResponse<T = unknown> {
  data?: T;
  status: number;
  error?: string;
  message?: string;
  timestamp?: string;
}

/**
 * Request payload for sending prompts
 */
export interface PromptRequest {
  prompt: string;
  context?: Record<string, unknown>;
}

/**
 * Response from prompt processing
 */
export interface PromptResponse {
  success: boolean;
  message: string;
  intent?: {
    service: string;
    action: string;
    parameters: Record<string, unknown>;
    confidence: number;
  };
  result?: {
    action: string;
    status: string;
    message: string;
    details: Record<string, unknown>;
  };
  execution_time: number;
  timestamp: string;
}

/**
 * Task status response
 */
export interface TaskStatusResponse {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  result?: unknown;
  error?: string;
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
}

/**
 * Authentication status response
 */
export interface AuthStatusResponse {
  authenticated: boolean;
  user?: {
    id: number;
    email: string;
    name: string;
    google_id?: string;
  };
  token_expires_at?: string;
  services_connected?: {
    gmail: boolean;
    calendar: boolean;
    tasks: boolean;
    keep: boolean;
    maps: boolean;
  };
}

/**
 * Service status response
 */
export interface ServiceStatusResponse {
  user: {
    id: number;
    email: string;
    name: string;
  };
  services: Record<string, {
    status: string;
    actions: number;
    note?: string;
  }>;
  gemini_ai: {
    status: string;
    model: string;
  };
}

/**
 * Error response structure
 */
export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: unknown;
  timestamp: string;
}

/**
 * OAuth URL response
 */
export interface OAuthUrlResponse {
  oauth_url: string;
  state: string;
}

// =============================================================================
// CONFIGURATION
// =============================================================================

/**
 * API Configuration
 */
class ApiConfig {
  private static instance: ApiConfig;
  
  public readonly baseURL: string;
  public readonly timeout: number;
  
  private constructor() {
    this.baseURL = (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_BASE_URL) || 'http://localhost:8000';
    this.timeout = 30000; // 30 seconds
  }
  
  public static getInstance(): ApiConfig {
    if (!ApiConfig.instance) {
      ApiConfig.instance = new ApiConfig();
    }
    return ApiConfig.instance;
  }
}

// =============================================================================
// TOKEN MANAGEMENT
// =============================================================================

/**
 * Token management utilities
 */
class TokenManager {
  private static readonly TOKEN_KEY = 'lume_auth_token';
  private static readonly REFRESH_TOKEN_KEY = 'lume_refresh_token';
  
  /**
   * Get the current authentication token
   */
  static getToken(): string | null {
    if (typeof window === 'undefined') return null;
    
    // Try to get from HTTP-only cookie first (most secure)
    const cookieToken = this.getCookieToken();
    if (cookieToken) return cookieToken;
    
    // Fallback to localStorage (less secure but more flexible)
    return localStorage.getItem(this.TOKEN_KEY);
  }
  
  /**
   * Set authentication token
   */
  static setToken(token: string): void {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem(this.TOKEN_KEY, token);
    
    // Also try to set as HTTP-only cookie if possible
    document.cookie = `${this.TOKEN_KEY}=${token}; path=/; secure; samesite=strict`;
  }
  
  /**
   * Get refresh token
   */
  static getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }
  
  /**
   * Set refresh token
   */
  static setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }
  
  /**
   * Clear all tokens
   */
  static clearTokens(): void {
    if (typeof window === 'undefined') return;
    
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    
    // Clear cookies
    document.cookie = `${this.TOKEN_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
  }
  
  /**
   * Get token from HTTP-only cookie
   */
  private static getCookieToken(): string | null {
    if (typeof document === 'undefined') return null;
    
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === this.TOKEN_KEY) {
        return value;
      }
    }
    return null;
  }
  
  /**
   * Check if token is expired (basic check)
   */
  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp < currentTime;
    } catch {
      return true; // If we can't parse it, consider it expired
    }
  }
}

// =============================================================================
// API CLIENT CLASS
// =============================================================================

/**
 * Main API Client class
 */
class LumeApiClient {
  private config: ApiConfig;
  private isRefreshing = false;
  private refreshPromise: Promise<string> | null = null;
  
  constructor() {
    this.config = ApiConfig.getInstance();
  }
  
  /**
   * Make HTTP request using fetch API
   */
  private async makeRequest<T = unknown>(config: HttpRequestConfig): Promise<HttpResponse<T>> {
    const startTime = Date.now();
    
    // Add auth token to headers
    const token = TokenManager.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    // Prepare fetch options
    const fetchOptions: RequestInit = {
      method: config.method,
      headers,
      body: config.body ? JSON.stringify(config.body) : undefined,
    };
    
    // Add timeout if specified
    const controller = new AbortController();
    if (config.timeout) {
      setTimeout(() => controller.abort(), config.timeout);
    }
    fetchOptions.signal = controller.signal;
    
    try {
      const response = await fetch(config.url, fetchOptions);
      const endTime = Date.now();
      
      console.debug(`API Request to ${config.url} took ${endTime - startTime}ms`);
      
      // Parse response
      let data: T;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = (await response.text()) as unknown as T;
      }
      
      // Convert headers to object
      const responseHeaders: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });
      
      const httpResponse: HttpResponse<T> = {
        data,
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
        config,
      };
      
      // Handle 401 Unauthorized - attempt token refresh
      if (response.status === 401 && !config._retry) {
        config._retry = true;
        
        try {
          const newToken = await this.refreshToken();
          
          // Retry with new token
          const retryHeaders = { ...headers, Authorization: `Bearer ${newToken}` };
          const retryConfig: HttpRequestConfig = {
            ...config,
            headers: retryHeaders,
          };
          
          return this.makeRequest<T>(retryConfig);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          this.handleAuthFailure();
          throw this.createHttpError(response, config, 'Token refresh failed');
        }
      }
      
      // Check for error status
      if (!response.ok) {
        throw this.createHttpError(response, config);
      }
      
      return httpResponse;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw this.createHttpError(null, config, 'Request timeout');
      }
      throw error;
    }
  }
  
  /**
   * Create HTTP error from response
   */
  private createHttpError(response: Response | null, config: HttpRequestConfig, message?: string): HttpError {
    const error = new Error(message || `HTTP ${response?.status || 0} Error`) as HttpError;
    
    if (response) {
      error.response = {
        status: response.status,
        statusText: response.statusText,
        data: null, // Would need to parse this separately if needed
      };
    }
    
    error.config = config;
    return error;
  }
  
  /**
   * Refresh authentication token
   */
  private async refreshToken(): Promise<string> {
    if (this.isRefreshing) {
      // If already refreshing, wait for the existing refresh to complete
      return this.refreshPromise!;
    }
    
    this.isRefreshing = true;
    
    this.refreshPromise = (async () => {
      try {
        const refreshToken = TokenManager.getRefreshToken();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        const response = await this.makeRequest<{ access_token: string; refresh_token?: string }>({
          method: 'POST',
          url: `${this.config.baseURL}/auth/refresh`,
          body: { refresh_token: refreshToken },
        });
        
        const { access_token, refresh_token: newRefreshToken } = response.data;
        
        TokenManager.setToken(access_token);
        if (newRefreshToken) {
          TokenManager.setRefreshToken(newRefreshToken);
        }
        
        return access_token;
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    })();
    
    return this.refreshPromise;
  }
  
  /**
   * Handle authentication failure
   */
  private handleAuthFailure(): void {
    TokenManager.clearTokens();
    
    // Redirect to login page
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }
  
  /**
   * Handle and format errors
   */
  private handleError(error: any): ApiError {
    const timestamp = new Date().toISOString();
    
    if (error && typeof error === 'object' && 'response' in error) {
      const httpError = error as HttpError;
      
      if (httpError.response) {
        // Server responded with error status
        return {
          message: httpError.response.data?.message || httpError.message,
          status: httpError.response.status,
          code: httpError.response.data?.code,
          details: httpError.response.data,
          timestamp,
        };
      } else if (httpError.config) {
        // Network error
        return {
          message: 'Network error - please check your connection',
          status: 0,
          code: 'NETWORK_ERROR',
          details: httpError.message,
          timestamp,
        };
      }
    }
    
    // Generic error
    return {
      message: error.message || 'An unexpected error occurred',
      status: 500,
      code: 'UNKNOWN_ERROR',
      details: error,
      timestamp,
    };
  }
  
  // =============================================================================
  // CORE API METHODS
  // =============================================================================
  
  /**
   * Send a natural language prompt to the backend
   */
  async sendPrompt(prompt: string, context?: Record<string, unknown>): Promise<ApiResponse<PromptResponse>> {
    try {
      const requestPayload: PromptRequest = {
        prompt: prompt.trim(),
        context,
      };
      
      console.debug('Sending prompt:', requestPayload);
      
      const response = await this.makeRequest<PromptResponse>({
        method: 'POST',
        url: `${this.config.baseURL}/api/prompt`,
        body: requestPayload,
      });
      
      return {
        data: response.data,
        status: response.status,
        message: 'Prompt processed successfully',
      };
    } catch (error) {
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Failed to process prompt',
      };
    }
  }
  
  /**
   * Get the status of an asynchronous task
   */
  async getTaskStatus(taskId: string): Promise<ApiResponse<TaskStatusResponse>> {
    try {
      if (!taskId || taskId.trim() === '') {
        throw new Error('Task ID is required');
      }
      
      console.debug('Getting task status:', taskId);
      
      const response = await this.makeRequest<TaskStatusResponse>({
        method: 'GET',
        url: `${this.config.baseURL}/api/tasks/${encodeURIComponent(taskId)}`,
      });
      
      return {
        data: response.data,
        status: response.status,
        message: 'Task status retrieved successfully',
      };
    } catch (error) {
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Failed to get task status',
      };
    }
  }
  
  /**
   * Check if the user is authenticated
   */
  async getAuthStatus(): Promise<boolean> {
    try {
      const token = TokenManager.getToken();
      
      // Quick check - if no token, definitely not authenticated
      if (!token) {
        return false;
      }
      
      // Check if token is expired (basic JWT check)
      if (TokenManager.isTokenExpired(token)) {
        try {
          // Try to refresh the token
          await this.refreshToken();
          return true;
        } catch {
          return false;
        }
      }
      
      // Verify with backend
      const response = await this.makeRequest<AuthStatusResponse>({
        method: 'GET',
        url: `${this.config.baseURL}/auth/me`,
      });
      
      return response.data.authenticated !== false; // Default to true if field missing
    } catch (error) {
      console.debug('Auth status check failed:', error);
      return false;
    }
  }
  
  /**
   * Get detailed authentication status
   */
  async getDetailedAuthStatus(): Promise<ApiResponse<AuthStatusResponse>> {
    try {
      const response = await this.makeRequest<AuthStatusResponse>({
        method: 'GET',
        url: `${this.config.baseURL}/auth/me`,
      });
      
      return {
        data: response.data,
        status: response.status,
        message: 'Authentication status retrieved successfully',
      };
    } catch (error) {
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Failed to get authentication status',
      };
    }
  }
  
  /**
   * Get service status and availability
   */
  async getServiceStatus(): Promise<ApiResponse<ServiceStatusResponse>> {
    try {
      const response = await this.makeRequest<ServiceStatusResponse>({
        method: 'GET',
        url: `${this.config.baseURL}/api/services/status`,
      });
      
      return {
        data: response.data,
        status: response.status,
        message: 'Service status retrieved successfully',
      };
    } catch (error) {
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Failed to get service status',
      };
    }
  }
  
  /**
   * Get Google OAuth URL for authentication
   */
  async getGoogleOAuthUrl(): Promise<ApiResponse<OAuthUrlResponse>> {
    try {
      const response = await this.makeRequest<OAuthUrlResponse>({
        method: 'GET',
        url: `${this.config.baseURL}/auth/oauth/google`,
      });
      
      return {
        data: response.data,
        status: response.status,
        message: 'OAuth URL generated successfully',
      };
    } catch (error) {
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Failed to get OAuth URL',
      };
    }
  }
  
  /**
   * Logout user and clear tokens
   */
  async logout(): Promise<ApiResponse<void>> {
    try {
      // Call backend logout endpoint if available
      try {
        await this.makeRequest({
          method: 'POST',
          url: `${this.config.baseURL}/auth/logout`,
        });
      } catch {
        // Ignore logout endpoint errors - still clear local tokens
      }
      
      // Clear local tokens
      TokenManager.clearTokens();
      
      return {
        status: 200,
        message: 'Logged out successfully',
      };
    } catch (error) {
      // Even if backend call fails, clear local tokens
      TokenManager.clearTokens();
      
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Logout completed (with warnings)',
      };
    }
  }
  
  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await this.makeRequest({
        method: 'GET',
        url: `${this.config.baseURL}/health`,
      });
      
      return {
        data: response.data,
        status: response.status,
        message: 'Health check successful',
      };
    } catch (error) {
      const apiError = this.handleError(error);
      return {
        status: apiError.status,
        error: apiError.message,
        message: 'Health check failed',
      };
    }
  }
}

// =============================================================================
// SINGLETON INSTANCE AND EXPORTS
// =============================================================================

/**
 * Singleton API client instance
 */
const apiClient = new LumeApiClient();

/**
 * Exported API functions for easy use
 */
export const api = {
  // Core functionality
  sendPrompt: (prompt: string, context?: Record<string, any>) => 
    apiClient.sendPrompt(prompt, context),
  
  getTaskStatus: (taskId: string) => 
    apiClient.getTaskStatus(taskId),
  
  getAuthStatus: () => 
    apiClient.getAuthStatus(),
  
  // Extended functionality
  getDetailedAuthStatus: () => 
    apiClient.getDetailedAuthStatus(),
  
  getServiceStatus: () => 
    apiClient.getServiceStatus(),
  
  getGoogleOAuthUrl: () => 
    apiClient.getGoogleOAuthUrl(),
  
  logout: () => 
    apiClient.logout(),
  
  healthCheck: () => 
    apiClient.healthCheck(),
};

/**
 * Token management utilities
 */
export const auth = {
  getToken: () => TokenManager.getToken(),
  setToken: (token: string) => TokenManager.setToken(token),
  getRefreshToken: () => TokenManager.getRefreshToken(),
  setRefreshToken: (token: string) => TokenManager.setRefreshToken(token),
  clearTokens: () => TokenManager.clearTokens(),
  isTokenExpired: (token: string) => TokenManager.isTokenExpired(token),
};

/**
 * Configuration access
 */
export const config = {
  baseURL: ApiConfig.getInstance().baseURL,
  timeout: ApiConfig.getInstance().timeout,
};

// Default export
export default api;

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Utility function to poll task status until completion
 */
export async function pollTaskStatus(
  taskId: string,
  options: {
    interval?: number;
    maxAttempts?: number;
    onProgress?: (status: TaskStatusResponse) => void;
  } = {}
): Promise<TaskStatusResponse> {
  const { interval = 2000, maxAttempts = 30, onProgress } = options;
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const response = await api.getTaskStatus(taskId);
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    const status = response.data!;
    
    if (onProgress) {
      onProgress(status);
    }
    
    if (status.status === 'completed' || status.status === 'failed') {
      return status;
    }
    
    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  throw new Error('Task polling timeout - maximum attempts reached');
}

/**
 * Utility function to check if the API is available
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await api.healthCheck();
    return response.status === 200;
  } catch {
    return false;
  }
}
