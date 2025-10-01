# LUME Frontend - Next.js Application

A beautiful, modern chat interface for the LUME AI Productivity Assistant, styled with Google's design language.

## Features

- 🎨 **Google-Themed UI** - Clean, modern interface following Google's design principles
- 💬 **Real-time Chat** - Seamless conversation interface with message history
- 🔐 **OAuth 2.0 Integration** - Secure Google authentication
- 📱 **Responsive Design** - Works beautifully on all devices
- 🎯 **Two-Stage Permissions** - Smart permission requesting based on user needs
- 📝 **Conversation History** - All your chats saved in the sidebar
- ⚡ **Fast & Optimized** - Built with Next.js 14 and TypeScript

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **State Management**: React Hooks

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend Django server running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
cd lume_frontend
npm install
```

2. Create environment file:
```bash
cp .env.local .env.local
```

3. Configure environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
lume_frontend/
├── src/
│   ├── app/
│   │   ├── globals.css          # Global styles with Google theme
│   │   ├── layout.tsx           # Root layout
│   │   └── page.tsx            # Main page with routing logic
│   ├── components/
│   │   ├── ChatInterface.tsx    # Main chat component
│   │   ├── Sidebar.tsx         # Conversation sidebar
│   │   ├── LoginScreen.tsx     # OAuth login screen
│   │   └── PermissionModal.tsx # Permission request modal
│   └── lib/
│       └── api.ts              # API client for backend
├── public/                      # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Features Breakdown

### Authentication Flow

1. User clicks "Sign in with Google"
2. Redirected to Google OAuth consent screen (base permissions only)
3. After successful auth, user is logged in
4. When user asks for a service-specific action, additional permissions are requested

### Two-Stage Permission System

**Stage 1: Base Permissions**
- Email
- Profile
- Contacts (for email addresses)

**Stage 2: Service Permissions** (requested dynamically)
- Gmail (if email-related request)
- Calendar (if calendar-related request)
- Tasks (if task-related request)
- Keep (if note-related request)

### Chat Interface

- Real-time message display
- Typing indicators
- Error handling
- Service detection badges
- Automatic scrolling
- Conversation history

### Sidebar Features

- New chat button
- Conversation list with timestamps
- User profile with avatar
- Active permissions display
- Logout functionality

## API Integration

The frontend communicates with the Django backend through the following endpoints:

### OAuth Endpoints
- `POST /api/oauth/initiate/` - Start OAuth flow
- `GET /oauth/callback/` - OAuth callback
- `POST /api/oauth/request-service-permissions/` - Request additional permissions

### User Endpoints
- `GET /api/user/info/` - Get current user info
- `POST /api/user/logout/` - Logout user

### Chat Endpoints
- `POST /api/chat/send/` - Send a message
- `GET /api/chat/conversations/` - Get conversation list
- `GET /api/chat/conversations/:id/` - Get conversation messages

## Styling Guide

### Color Palette (Google Theme)

- **Blue** (#4285F4) - Primary actions, Gmail
- **Red** (#EA4335) - Calendar, warnings
- **Yellow** (#FBBC04) - Tasks, highlights
- **Green** (#34A853) - Keep, success states
- **Gray** (#F8F9FA) - Backgrounds, neutral elements

### Typography

- **Font Family**: Google Sans, Roboto, Arial
- **Headings**: Bold (700), semibold (600)
- **Body**: Regular (400), medium (500)

## Development Tips

### Adding New Components

1. Create component in `src/components/`
2. Use TypeScript for type safety
3. Follow the existing naming conventions
4. Add proper props interfaces

### API Client Usage

```typescript
import { apiClient } from '@/lib/api';

// Send a message
const response = await apiClient.sendMessage('Hello', conversationId);

// Get user info
const user = await apiClient.getUserInfo();
```

### Styling with Tailwind

Use Google theme colors:
```tsx
<button className="bg-google-blue text-white hover:bg-blue-600">
  Click me
</button>
```

## Troubleshooting

### CORS Issues

Ensure Django backend has CORS configured:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True
```

### API Connection Failed

1. Check backend is running on port 8000
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for errors

### OAuth Redirect Issues

1. Verify redirect URI matches in Google Cloud Console
2. Check Django `GOOGLE_REDIRECT_URI` setting
3. Ensure `FRONTEND_URL` is correctly set in Django

## Contributing

1. Follow the existing code style
2. Add TypeScript types for all new code
3. Test OAuth flows thoroughly
4. Ensure responsive design works

## License

MIT License - See LICENSE file for details
