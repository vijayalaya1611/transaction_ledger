from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import TransferCreate, TransferResponse
from app import crud

router = APIRouter(prefix="/transfers", tags=["Transfers (Bonus)"])

@router.post("", response_model=TransferResponse, status_code=status.HTTP_200_OK, summary="Atomic money transfer")
async def transfer_funds(transfer_in: TransferCreate, db: AsyncSession = Depends(get_db)):
    """
    Executes an atomic transfer between two accounts.
    Locks both accounts in a deterministic order to eliminate deadlocks.
    """
    return await crud.transfer_money(db, transfer_in)
