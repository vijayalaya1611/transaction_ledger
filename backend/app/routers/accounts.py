from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    AccountCreate,
    AccountResponse,
    AccountBalanceResponse,
    TransactionPaginationResponse,
    TransactionResponse
)
from app import crud

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED, summary="Create a new account")
async def create_new_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates an account with an initial balance of 0.
    The client cannot set the initial balance.
    """
    account = await crud.create_account(db, account_in)
    return account

@router.get("", response_model=List[AccountResponse], summary="List all accounts")
async def list_all_accounts(db: AsyncSession = Depends(get_db)):
    """Fetches all accounts (useful for the UI dashboard)."""
    return await crud.get_all_accounts(db)

@router.get("/{account_id}/balance", response_model=AccountBalanceResponse, summary="Get current account balance")
async def get_balance(account_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches current balance of the specified account."""
    account = await crud.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "ACCOUNT_NOT_FOUND", "message": f"Account '{account_id}' was not found"}
        )
    return AccountBalanceResponse(account_id=account.id, balance=account.balance)

@router.get("/{account_id}/transactions", response_model=TransactionPaginationResponse, summary="Get transaction history")
async def get_transactions(
    account_id: str,
    type: Optional[str] = Query(None, description="Filter by transaction type: 'credit' or 'debit'"),
    page: int = Query(1, ge=1, description="Page number, minimum 1"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (1 to 100)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves sorted, paginated transactions for the specified account in latest-first order.
    """
    items, total_records, total_pages = await crud.get_account_transactions(
        db=db,
        account_id=account_id,
        tx_type=type,
        page=page,
        limit=limit
    )

    return TransactionPaginationResponse(
        current_page=page,
        page_size=limit,
        total_records=total_records,
        total_pages=total_pages,
        transactions=[TransactionResponse.model_validate(t) for t in items]
    )
