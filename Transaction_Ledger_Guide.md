# Transaction Ledger API - Deployment Guide

## Overview
This is a full-stack transaction ledger system with:
- Backend: Python FastAPI API with PostgreSQL database
- Frontend: React application (not implemented yet)
- Database: Supabase (free tier PostgreSQL)
- Deployment: AWS free tier + Render (free backend hosting)

## Step 1: Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and sign up
2. Create a new project:
   - Choose a name (e.g., "transaction-ledger")
   - Set a database password (save it somewhere safe)
   - Wait for project to initialize (takes ~2-5 minutes)
3. Get your connection details:
   - Project URL (e.g., `https://xyz123.supabase.co`)
   - API key (found in Project Settings > API)
   - Database URL (e.g., `postgresql://postgres:password@xyz123.supabase.co:5432/postgres`)

## Step 2: Configure Environment Variables

Create a `.env` file in your project root:

```env
# Supabase configuration
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>

# API configuration
API_BASE_URL=http://localhost:8000  # Will change after deployment
```

## Step 3: Run Locally (Development)

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables)
python src/database/init_db.py

# Start development server
uvicorn src.api.main:app --reload --port 8000
```

### Frontend (React)

```bash
# Navigate to frontend directory
cd transaction-ledger-frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Step 4: Deploy Backend to Render (Free Tier)

### Option A: Render Web Service (Recommended)

1. Go to [render.com](https://render.com) and sign up
2. Create a new Web Service:
   - Connect your GitHub repository
   - Set build command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - Set start command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - Set environment variables:
     - `DATABASE_URL`: Your Supabase database URL
     - `API_BASE_URL`: Will be set automatically after deployment
3. Deploy the service

### Option B: Deploy to AWS (EC2 + RDS)

1. Create an AWS account (free tier)
2. Set up EC2 instance (Ubuntu) with security group allowing port 8000
3. Set up RDS PostgreSQL (use Supabase or create your own)
4. Deploy your code to EC2
5. Configure environment variables

## Step 5: Deploy Frontend to Netlify (Free Tier)

1. Go to [netlify.com](https://netlify.com) and sign up
2. Create a new site from GitHub:
   - Connect your frontend repository
   - Set build command: `npm run build`
   - Set publish directory: `dist`
3. Deploy the site

## Step 6: Configure Environment Variables for Deployment

### For Render Backend:
- Set `DATABASE_URL` to your Supabase connection string
- Set `API_BASE_URL` to your Render service URL (e.g., `https://your-app.onrender.com`)

### For Netlify Frontend:
- Set `REACT_APP_API_BASE_URL` to your Render service URL

## Database Setup

### Create Tables
Run this command to initialize the database schema:

```bash
python src/database/init_db.py
```

This creates the `accounts` and `transactions` tables with proper constraints.

## API Endpoints

### Accounts
- `POST /accounts` - Create new account (requires name)
- `GET /accounts/{id}` - Get account details

### Transactions
- `POST /transactions` - Add transaction (requires account_id, type, amount)
- `GET /transactions` - Get transaction history (supports filtering/pagination)

### Transfers (Bonus)
- `POST /transfers` - Transfer money between accounts (atomic operation)

## Error Handling
All endpoints return proper HTTP status codes:
- 400: Bad request (invalid data)
- 404: Not found (account/transaction not found)
- 409: Conflict (duplicate reference_id)
- 422: Unprocessable entity (insufficient balance, invalid amount)

## Testing
Run tests with:
```bash
pytest tests/ -v
```

## Key Requirements Met
✅ Account creation with balance starting at 0
✅ Credit/debit transactions with validation
✅ Duplicate reference_id prevention per account
✅ Balance consistency and atomicity
✅ Immutable transactions
✅ Pagination, filtering, and sorting in history endpoint
✅ Proper error handling with HTTP status codes
✅ Clean project structure
✅ Deployable to free tiers (Supabase + Render + Netlify)