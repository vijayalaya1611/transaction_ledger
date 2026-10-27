# Transaction Ledger System

A production-ready full-stack Transaction Ledger application designed to maintain strict financial data integrity, ACID compliance, idempotency, and concurrency protection.

Built with **FastAPI (Python)**, **PostgreSQL (Supabase)**, and **React (Vite)**.

---

## 🌟 Architecture Overview

```
                      ┌────────────────────────────┐
                      │    React.js Dashboard      │
                      │    (Hosted on Netlify)     │
                      └─────────────┬──────────────┘
                                    │ HTTP / JSON
                                    ▼
                      ┌────────────────────────────┐
                      │    FastAPI Backend API     │
                      │    (Hosted on Render)      │
                      │  - Automatic /docs Swagger │
                      │  - Pydantic Validation     │
                      │  - Row-Level Locking       │
                      └─────────────┬──────────────┘
                                    │ Connection Pooling / SSL
                                    ▼
                      ┌────────────────────────────┐
                      │   Supabase PostgreSQL DB   │
                      │  - ACID Transactions       │
                      │  - Compound Unique Keys    │
                      │  - Check Constraints       │
                      └────────────────────────────┘
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- A **Supabase PostgreSQL** database (free tier, no credit card required)

### 2. Backend Setup
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `backend/.env`:
   ```ini
   DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   CORS_ORIGINS=*
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Alternative ReDoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 3. Frontend Setup
1. Open a new terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📡 API Specification & Documentation

FastAPI auto-generates interactive OpenAPI documentation at `/docs`. Below is the complete API specification:

### 1. Create Account
- **Endpoint**: `POST /api/accounts`
- **Description**: Creates a new account. The system guarantees the initial balance is `0.00`.
- **Request Body**:
  ```json
  {
    "name": "Alice Cooper"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
    "name": "Alice Cooper",
    "balance": "0.00",
    "created_at": "2026-10-27T20:00:00Z"
  }
  ```

---

### 2. Add Transaction
- **Endpoint**: `POST /api/transactions`
- **Description**: Atomically credits or debits an account.
- **Rules**:
  - `credit`: Increases account balance by `amount`.
  - `debit`: Decreases account balance. **Rejected with `400 Bad Request` if balance is insufficient.**
  - `idempotency`: `reference_id` must be unique per account. Duplicate submissions return `409 Conflict` and do not alter the balance.
- **Request Body**:
  ```json
  {
    "account_id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
    "type": "credit",
    "amount": 100.50,
    "reference_id": "DEP-2026-001",
    "description": "Salary deposit"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "id": "a988d8b1-3e5b-4c07-b379-994fa4698539",
    "account_id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
    "type": "credit",
    "amount": "100.50",
    "reference_id": "DEP-2026-001",
    "description": "Salary deposit",
    "created_at": "2026-10-27T20:05:00Z"
  }
  ```

---

### 3. Get Account Balance
- **Endpoint**: `GET /api/accounts/{account_id}/balance`
- **Description**: Returns the real-time balance of the account.
- **Response** (`200 OK`):
  ```json
  {
    "account_id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
    "balance": "100.50"
  }
  ```

---

### 4. Get Transaction History
- **Endpoint**: `GET /api/accounts/{account_id}/transactions`
- **Query Parameters**:
  - `type` *(optional)*: `credit` | `debit` (returns both if omitted)
  - `page` *(optional, default 1)*: Page number ($\ge 1$)
  - `limit` *(optional, default 10)*: Page size (1 to 100)
- **Sorting**: Latest transactions first (`created_at DESC`).
- **Response** (`200 OK`):
  ```json
  {
    "current_page": 1,
    "page_size": 10,
    "total_records": 1,
    "total_pages": 1,
    "transactions": [
      {
        "id": "a988d8b1-3e5b-4c07-b379-994fa4698539",
        "account_id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
        "type": "credit",
        "amount": "100.50",
        "reference_id": "DEP-2026-001",
        "description": "Salary deposit",
        "created_at": "2026-10-27T20:05:00Z"
      }
    ]
  }
  ```

---

### 5. Money Transfer (Bonus Feature)
- **Endpoint**: `POST /api/transfers`
- **Description**: Transfers funds between two distinct accounts atomically.
- **Request Body**:
  ```json
  {
    "source_account_id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
    "destination_account_id": "f5c7d812-3b44-4f89-8d23-76cb5723741b",
    "amount": 35.00,
    "reference_id": "TRF-9001",
    "description": "Shared expense"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "status": "success",
    "message": "Successfully transferred 35.00 from Alice Cooper to Bob Dylan",
    "amount": "35.00",
    "source_account_id": "e4b6c934-2e55-4e78-9e12-87db6812839a",
    "destination_account_id": "f5c7d812-3b44-4f89-8d23-76cb5723741b",
    "source_balance": "65.50",
    "source_transaction_id": "...",
    "destination_transaction_id": "..."
  }
  ```

---

## 🔒 Assumptions & Key Design Decisions

1. **Currency Precision (No Floating-Point Drift)**:
   - Floating-point representations (`float` / `double`) introduce catastrophic precision errors in financial accounting.
   - All monetary amounts are stored using PostgreSQL's **`NUMERIC(12, 2)`** and Python's **`Decimal`**, enforcing 2 decimal places and absolute mathematical accuracy.

2. **Race Condition Prevention (Pessimistic Row Locking)**:
   - When processing a transaction, the account row is acquired using `SELECT ... FOR UPDATE`.
   - Concurrent requests for the same account must wait their turn, guaranteeing that debit requests never overdraft an account due to simultaneous reads.

3. **Compound Idempotency Constraint**:
   - The assessment requires that `reference_id` must be unique for the same account, while different accounts may reuse reference IDs.
   - We enforce this at the database engine level via:
     ```sql
     CONSTRAINT uq_account_reference UNIQUE (account_id, reference_id)
     ```
   - Duplicate attempts trigger a `409 Conflict` without modifying account state.

4. **Transfer Deadlock Avoidance**:
   - In circular concurrent transfers (e.g. Account A $\rightarrow$ Account B while Account B $\rightarrow$ Account A), deadlocks can occur if locks are obtained in arbitrary order.
   - We eliminate deadlocks by sorting the account IDs alphabetically and locking them in deterministic order (`sorted([source_id, dest_id])`).

5. **Ledger Immutability**:
   - Per double-entry ledger design standards, transactions are strictly write-only / append-only.
   - There are no `PUT`, `PATCH`, or `DELETE` endpoints for transactions. Erroneous transactions must be countered with compensatory ledger entries.

---

## ☁️ Free-Tier Cloud Deployment Guide

### 1. Database (Supabase)
1. Sign up at [supabase.com](https://supabase.com) (free forever, no credit card needed).
2. Create project `confluencr-ledger`.
3. In **SQL Editor**, run the schema provided in `backend/app/models.py`.
4. Copy the connection string under **Project Settings $\rightarrow$ Database $\rightarrow$ Connection URI**.

### 2. Backend (Render)
1. Push repository to GitHub.
2. Sign up at [render.com](https://render.com) (free tier).
3. Create a **New Web Service** pointing to your repository:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `DATABASE_URL`: *(Your Supabase connection string)*
     - `CORS_ORIGINS`: `*`

### 3. Frontend (Netlify)
1. Sign up at [netlify.com](https://netlify.com) (free tier).
2. Click **Add new site $\rightarrow$ Import an existing project** from GitHub.
3. Configure build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Environment Variable**: `VITE_API_BASE_URL` = `https://<your-render-app>.onrender.com/api`
