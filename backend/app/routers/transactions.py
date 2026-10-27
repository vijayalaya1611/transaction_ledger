from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import TransactionCreate, TransactionResponse
from app import crud

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Add a transaction")
async def add_transaction(tx_in: TransactionCreate, db: AsyncSession = Depends(get_db)):
    """
    Adds a credit or debit transaction to an account.
    - Credit: increases account balance.
    - Debit: decreases account balance (rejected if insufficient balance).
    - Idempotency: Duplicate reference_id for the same account is rejected.
    """
    transaction = await crud.add_transaction(db, tx_in)
    return transaction
