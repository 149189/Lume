# LUME - Complete Setup Guide

This guide will walk you through setting up the complete LUME application from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MySQL Database Setup](#mysql-database-setup)
3. [Google Cloud Console Configuration](#google-cloud-console-configuration)
4. [Django Backend Setup](#django-backend-setup)
5. [Next.js Frontend Setup](#nextjs-frontend-setup)
6. [Running the Application](#running-the-application)
7. [Testing the OAuth Flow](#testing-the-oauth-flow)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.10 or higher**
  - Download: https://www.python.org/downloads/
  - Verify: `python --version`

- **Node.js 18 or higher**
  - Download: https://nodejs.org/
  - Verify: `node --version` and `npm --version`

- **MySQL 8.0 or higher**
  - Download: https://dev.mysql.com/downloads/mysql/
  - Verify: `mysql --version`

- **Git** (optional but recommended)
  - Download: https://git-scm.com/downloads

---

## MySQL Database Setup

### Step 1: Start MySQL Server

Make sure your MySQL server is running. On Windows, you can start it from Services or MySQL Workbench.

### Step 2: Create Database

Open MySQL command line or MySQL Workbench and run:

```sql
CREATE DATABASE gmail_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 3: Verify Database Creation

```sql
SHOW DATABASES;
USE gmail_agent;
```

### Step 4: Create User (Optional but Recommended)

If you want to use a dedicated user instead of root:

```sql
CREATE USER 'lume_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON gmail_agent.* TO 'lume_user'@'localhost';
FLUSH PRIVILEGES;
```

**Note:** Update your `.env` file with these credentials if you create a new user.

---

## Google Cloud Console Configuration

### Step 1: Create/Select Project

1. Go to https://console.cloud.google.com/
2. Click on project dropdown at the top
3. Click "New Project" or select an existing one
4. Name it something like "LUME-Assistant"

### Step 2: Enable Required APIs

Go to "APIs & Services" > "Library" and enable:

1. **Gmail API**
   - Search for "Gmail API"
   - Click "Enable"

2. **Google Calendar API**
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Google Tasks API**
   - Search for "Tasks API"
   - Click "Enable"

4. **People API**
   - Search for "People API"
   - Click "Enable"

5. **Google Keep API** (if available)
   - Search for "Keep API"
   - Click "Enable" (Note: May not be publicly available)

### Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type
3. Click "Create"
4. Fill in required fields:
   - **App name:** LUME AI Assistant
   - **User support email:** Your email
   - **Developer contact email:** Your email
5. Click "Save and Continue"
6. On "Scopes" page, click "Add or Remove Scopes"
7. Add the following scopes:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `.../auth/gmail.readonly`
   - `.../auth/gmail.send`
   - `.../auth/gmail.modify`
   - `.../auth/calendar`
   - `.../auth/calendar.events`
   - `.../auth/tasks`
   - `.../auth/contacts.readonly`
8. Click "Save and Continue"
9. Add test users (your email) on the "Test users" page
10. Click "Save and Continue"

### Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Name it "LUME Web Client"
5. Add Authorized JavaScript origins:
   - `http://localhost:3000`
   - `http://localhost:8000`
6. Add Authorized redirect URIs:
   - `http://localhost:8000/oauth/callback/`
   - `http://localhost:8000/oauth/service-callback/`
7. Click "Create"
8. **IMPORTANT:** Copy your Client ID and Client Secret
9. Save them securely - you'll need them for the `.env` file

---

## Django Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd C:\Users\kaust\OneDrive\Documents\GitHub\Lume\lume_django
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# You should see (venv) in your command prompt
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Django 4.2.7
- mysqlclient
- django-cors-headers
- google-auth packages
- google-api-python-client

### Step 4: Create Environment File

```bash
# Copy the example file
copy .env.example .env
```

Now edit `.env` file with your actual values:

```env
# Database Configuration
DB_NAME=gmail_agent
DB_USER=root
DB_PASSWORD=Kaustubh@149
DB_HOST=127.0.0.1
DB_PORT=3306

# Django Secret Key
SECRET_KEY=django-insecure-0#ffbqnw1e4e8ltzrw-#br=2qon@fepni)d)n9g^#75o$h$l4$

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_actual_client_id_from_google_console
GOOGLE_CLIENT_SECRET=your_actual_client_secret_from_google_console
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback/

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Debug Mode
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Step 5: Run Database Migrations

```bash
# Create migration files
python manage.py makemigrations oauth
python manage.py makemigrations service_detector

# Apply migrations
python manage.py migrate
```

You should see output like:
```
Running migrations:
  Applying oauth.0001_initial... OK
  Applying oauth.0002_auto... OK
  ...
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Step 7: Test the Server

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

Open `http://localhost:8000/admin` in your browser to verify Django is running.

**Keep this terminal window open and running.**

---

## Next.js Frontend Setup

### Step 1: Open New Terminal

Open a **new** terminal window (keep Django running in the first one).

### Step 2: Navigate to Frontend Directory

```bash
cd C:\Users\kaust\OneDrive\Documents\GitHub\Lume\lume_frontend
```

### Step 3: Install Dependencies

```bash
npm install
```

This will install:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Axios
- Lucide React icons

### Step 4: Verify Environment Variables

Check that `.env.local` exists with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 5: Run Development Server

```bash
npm run dev
```

You should see:
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

---

## Running the Application

### You Should Now Have Two Terminals Running:

**Terminal 1 - Django Backend:**
```bash
cd lume_django
venv\Scripts\activate
python manage.py runserver
# Running on http://localhost:8000
```

**Terminal 2 - Next.js Frontend:**
```bash
cd lume_frontend
npm run dev
# Running on http://localhost:3000
```

### Access the Application

1. Open browser to: `http://localhost:3000`
2. You should see the LUME login screen with Google-themed UI

---

## Testing the OAuth Flow

### Step 1: Initial Login

1. Click "Sign in with Google" button
2. You'll be redirected to Google OAuth consent screen
3. Grant the base permissions (email, profile, contacts)
4. You'll be redirected back to LUME
5. You should now see the chat interface

### Step 2: Test Service Detection

Try these prompts to test different services:

**Email (Gmail):**
```
Send an email to test@example.com saying hello
```

**Calendar:**
```
Schedule a meeting for tomorrow at 2 PM
```

**Tasks:**
```
Create a task to review the project proposal
```

**Multiple Services:**
```
Send an email and create a task about the meeting
```

### Step 3: Grant Service Permissions

When you try a service-specific action:

1. You'll see a permission modal appear
2. Select which services you want to grant access to
3. Click "Grant Access"
4. You'll be redirected to Google to approve those specific permissions
5. After approval, you'll return to LUME and can complete the action

---

## Troubleshooting

### Database Connection Issues

**Error:** `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**Solution:**
- Ensure MySQL server is running
- Verify credentials in `.env` file
- Check if port 3306 is not blocked

### Google OAuth Errors

**Error:** `redirect_uri_mismatch`

**Solution:**
- Verify redirect URIs in Google Cloud Console match exactly:
  - `http://localhost:8000/oauth/callback/`
  - `http://localhost:8000/oauth/service-callback/`
- No trailing spaces or extra characters

**Error:** `invalid_client`

**Solution:**
- Double-check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in `.env`
- Ensure no extra spaces or quotes around values

### CORS Errors

**Error:** `Access-Control-Allow-Origin header is missing`

**Solution:**
- Verify Django settings include:
  ```python
  CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
  CORS_ALLOW_CREDENTIALS = True
  ```
- Restart Django server after changing settings

### Frontend Not Connecting to Backend

**Error:** `Network Error` or `Failed to fetch`

**Solution:**
- Ensure Django is running on port 8000
- Check `.env.local` has correct API URL: `http://localhost:8000`
- Try accessing `http://localhost:8000/api/user/info/` directly

### Port Already in Use

**Error:** `Port 8000 is already in use` or `Port 3000 is already in use`

**Solution:**
```bash
# Windows - Kill process on port
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Or use different ports
python manage.py runserver 8001
npm run dev -- -p 3001
```

### Module Import Errors in Frontend

**Error:** TypeScript errors about missing modules

**Solution:**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Restart VS Code or your editor

---

## Next Steps

### 1. Explore the Admin Panel

Visit `http://localhost:8000/admin` and login with your superuser account to:
- View users and their permissions
- Check conversation history
- Monitor OAuth states
- View chat messages

### 2. Customize the Application

- Modify chat interface styling in `lume_frontend/src/components/`
- Add new service handlers in `lume_django/oauth/views.py`
- Extend the service detector in `lume_django/service_detector/`

### 3. Production Deployment

Before deploying to production:
- Change `DEBUG=False` in Django settings
- Use strong `SECRET_KEY`
- Set up proper database with backups
- Configure HTTPS for OAuth callbacks
- Update Google OAuth redirect URIs to production URLs
- Set up proper error logging
- Configure static file serving

---

## Support

If you encounter issues not covered in this guide:

1. Check Django error logs in terminal
2. Check browser console for JavaScript errors
3. Verify all environment variables are set correctly
4. Ensure all services (MySQL, Django, Next.js) are running
5. Review Google Cloud Console for API quota issues

## Summary

You now have a fully functional LUME AI Assistant with:
- ✅ Django REST backend with OAuth 2.0
- ✅ Next.js frontend with beautiful Google-themed UI
- ✅ MySQL database for persistent storage
- ✅ Two-stage permission system
- ✅ Real-time chat interface
- ✅ Service detection and routing

Enjoy using LUME! 🌟
