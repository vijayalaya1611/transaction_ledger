import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_create_account():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create account
        response = await ac.post("/api/accounts", json={"name": "Alice Cooper"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Alice Cooper"
        assert float(data["balance"]) == 0.0
        assert "id" in data
        assert "created_at" in data

@pytest.mark.asyncio
async def test_credit_and_debit_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create account
        acc_res = await ac.post("/api/accounts", json={"name": "Bob Marley"})
        assert acc_res.status_code == 201
        acc_id = acc_res.json()["id"]

        # 2. Credit 100.00
        tx1 = await ac.post("/api/transactions", json={
            "account_id": acc_id,
            "type": "credit",
            "amount": 100.00,
            "reference_id": "TX-1001",
            "description": "Salary deposit"
        })
        assert tx1.status_code == 201
        assert float(tx1.json()["amount"]) == 100.00

        # Check balance
        bal1 = await ac.get(f"/api/accounts/{acc_id}/balance")
        assert bal1.status_code == 200
        assert float(bal1.json()["balance"]) == 100.00

        # 3. Debit 30.00
        tx2 = await ac.post("/api/transactions", json={
            "account_id": acc_id,
            "type": "debit",
            "amount": 30.00,
            "reference_id": "TX-1002",
            "description": "Coffee shop"
        })
        assert tx2.status_code == 201
        
        # Check balance again -> should be 70.00
        bal2 = await ac.get(f"/api/accounts/{acc_id}/balance")
        assert bal2.status_code == 200
        assert float(bal2.json()["balance"]) == 70.00

@pytest.mark.asyncio
async def test_debit_insufficient_balance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        acc_res = await ac.post("/api/accounts", json={"name": "Charlie Puth"})
        acc_id = acc_res.json()["id"]

        # Account has 0.00 balance, try to debit 50.00
        tx = await ac.post("/api/transactions", json={
            "account_id": acc_id,
            "type": "debit",
            "amount": 50.00,
            "reference_id": "TX-FAIL-1",
            "description": "Overdraft attempt"
        })
        assert tx.status_code == 400
        data = tx.json()
        assert data["detail"]["error"] == "INSUFFICIENT_BALANCE"

        # Verify balance is still 0.00
        bal = await ac.get(f"/api/accounts/{acc_id}/balance")
        assert float(bal.json()["balance"]) == 0.00

@pytest.mark.asyncio
async def test_duplicate_reference_id_idempotency():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Account 1
        acc1 = (await ac.post("/api/accounts", json={"name": "Dave Dave"})).json()["id"]
        # Create Account 2
        acc2 = (await ac.post("/api/accounts", json={"name": "Emma Watson"})).json()["id"]

        # First transaction on Account 1
        res1 = await ac.post("/api/transactions", json={
            "account_id": acc1,
            "type": "credit",
            "amount": 50.00,
            "reference_id": "REF-SHARED-123"
        })
        assert res1.status_code == 201

        # Duplicate transaction on SAME Account 1 -> MUST BE REJECTED with 409
        res2 = await ac.post("/api/transactions", json={
            "account_id": acc1,
            "type": "credit",
            "amount": 50.00,
            "reference_id": "REF-SHARED-123"
        })
        assert res2.status_code == 409
        assert res2.json()["detail"]["error"] == "DUPLICATE_TRANSACTION"

        # Balance on Account 1 must still be 50.00 (not 100.00)
        bal1 = await ac.get(f"/api/accounts/{acc1}/balance")
        assert float(bal1.json()["balance"]) == 50.00

        # Same reference_id on DIFFERENT Account 2 -> MUST SUCCEED
        res3 = await ac.post("/api/transactions", json={
            "account_id": acc2,
            "type": "credit",
            "amount": 75.00,
            "reference_id": "REF-SHARED-123"
        })
        assert res3.status_code == 201

@pytest.mark.asyncio
async def test_transaction_history_filtering_and_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        acc_id = (await ac.post("/api/accounts", json={"name": "Frank Castle"})).json()["id"]

        # Add 3 credits and 2 debits
        for i in range(1, 4):
            await ac.post("/api/transactions", json={
                "account_id": acc_id,
                "type": "credit",
                "amount": float(i * 10),
                "reference_id": f"HIST-CR-{i}"
            })
        for i in range(1, 3):
            await ac.post("/api/transactions", json={
                "account_id": acc_id,
                "type": "debit",
                "amount": float(i * 5),
                "reference_id": f"HIST-DB-{i}"
            })

        # Test filter: credit only
        cr_res = await ac.get(f"/api/accounts/{acc_id}/transactions?type=credit")
        assert cr_res.status_code == 200
        cr_data = cr_res.json()
        assert cr_data["total_records"] == 3
        assert all(t["type"] == "credit" for t in cr_data["transactions"])

        # Test filter: debit only
        db_res = await ac.get(f"/api/accounts/{acc_id}/transactions?type=debit")
        assert db_res.status_code == 200
        db_data = db_res.json()
        assert db_data["total_records"] == 2
        assert all(t["type"] == "debit" for t in db_data["transactions"])

        # Test pagination: limit=2
        p1_res = await ac.get(f"/api/accounts/{acc_id}/transactions?page=1&limit=2")
        assert p1_res.status_code == 200
        p1_data = p1_res.json()
        assert len(p1_data["transactions"]) == 2
        assert p1_data["total_records"] == 5
        assert p1_data["total_pages"] == 3

@pytest.mark.asyncio
async def test_atomic_money_transfer():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create sender and receiver
        sender = (await ac.post("/api/accounts", json={"name": "Sender Acc"})).json()["id"]
        receiver = (await ac.post("/api/accounts", json={"name": "Receiver Acc"})).json()["id"]

        # Fund sender with 100.00
        await ac.post("/api/transactions", json={
            "account_id": sender,
            "type": "credit",
            "amount": 100.00,
            "reference_id": "INIT-FUND-1"
        })

        # Transfer 40.00
        trf_res = await ac.post("/api/transfers", json={
            "source_account_id": sender,
            "destination_account_id": receiver,
            "amount": 40.00,
            "reference_id": "TRF-001",
            "description": "Lunch split"
        })
        assert trf_res.status_code == 200
        assert trf_res.json()["status"] == "success"

        # Verify balances: Sender 60.00, Receiver 40.00
        s_bal = (await ac.get(f"/api/accounts/{sender}/balance")).json()["balance"]
        r_bal = (await ac.get(f"/api/accounts/{receiver}/balance")).json()["balance"]
        assert float(s_bal) == 60.00
        assert float(r_bal) == 40.00

        # Try to transfer more than available balance (e.g. 70.00) -> MUST FAIL
        fail_res = await ac.post("/api/transfers", json={
            "source_account_id": sender,
            "destination_account_id": receiver,
            "amount": 70.00,
            "reference_id": "TRF-FAIL-OVERDRAFT"
        })
        assert fail_res.status_code == 400
        assert fail_res.json()["detail"]["error"] == "INSUFFICIENT_BALANCE"
