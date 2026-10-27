import math
from decimal import Decimal
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models import Account, Transaction
from app.schemas import AccountCreate, TransactionCreate, TransactionType, TransferCreate

class LedgerException(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(status_code=status_code, detail={"error": error_code, "message": message})

async def create_account(db: AsyncSession, account_in: AccountCreate) -> Account:
    """Creates a new account with guaranteed initial balance of 0."""
    account = Account(
        name=account_in.name,
        balance=Decimal("0.00")  # Strictly forced by system, cannot be set by client
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account

async def get_account(db: AsyncSession, account_id: str) -> Optional[Account]:
    """Retrieve an account by its ID."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    return result.scalar_one_or_none()

async def get_all_accounts(db: AsyncSession) -> List[Account]:
    """Retrieve all accounts (useful for UI/testing)."""
    result = await db.execute(select(Account).order_by(Account.created_at.desc()))
    return result.scalars().all()

async def add_transaction(db: AsyncSession, tx_in: TransactionCreate) -> Transaction:
    """
    Executes a transaction atomically with row-level locking.
    Handles duplicate reference_ids, balance validation, and balance update.
    """
    # 1. Check for duplicate reference_id for this specific account
    dup_stmt = select(Transaction).where(
        and_(
            Transaction.account_id == tx_in.account_id,
            Transaction.reference_id == tx_in.reference_id
        )
    )
    dup_result = await db.execute(dup_stmt)
    existing_tx = dup_result.scalar_one_or_none()
    if existing_tx:
        raise LedgerException(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_TRANSACTION",
            message=f"Transaction with reference_id '{tx_in.reference_id}' already exists for account '{tx_in.account_id}'"
        )

    # 2. Acquire row lock on the account to prevent race conditions (SELECT ... FOR UPDATE)
    stmt = select(Account).where(Account.id == tx_in.account_id).with_for_update()
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise LedgerException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ACCOUNT_NOT_FOUND",
            message=f"Account '{tx_in.account_id}' does not exist"
        )

    # 3. Validate Debit balance constraint
    amount = Decimal(str(tx_in.amount))
    if tx_in.type == TransactionType.DEBIT:
        if account.balance < amount:
            raise LedgerException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="INSUFFICIENT_BALANCE",
                message=f"Account balance ({account.balance}) is insufficient for debit amount ({amount})"
            )
        account.balance -= amount
    else:
        account.balance += amount

    # 4. Create Transaction record
    tx = Transaction(
        account_id=account.id,
        type=tx_in.type.value,
        amount=amount,
        description=tx_in.description,
        reference_id=tx_in.reference_id
    )
    db.add(tx)

    # 5. Persist both balance update and transaction atomically
    try:
        await db.commit()
        await db.refresh(tx)
        return tx
    except IntegrityError as e:
        await db.rollback()
        # Handle concurrent race insertion of same reference_id
        if "uq_account_reference" in str(e).lower() or "unique constraint" in str(e).lower():
            raise LedgerException(
                status_code=status.HTTP_409_CONFLICT,
                error_code="DUPLICATE_TRANSACTION",
                message=f"Transaction with reference_id '{tx_in.reference_id}' already exists"
            )
        raise LedgerException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            message="An error occurred while persisting the transaction"
        )

async def get_account_transactions(
    db: AsyncSession,
    account_id: str,
    tx_type: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> Tuple[List[Transaction], int, int]:
    """
    Fetches paginated transactions for an account sorted in latest-first order.
    Returns: (transactions, total_records, total_pages)
    """
    # Verify account exists
    account = await get_account(db, account_id)
    if not account:
        raise LedgerException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ACCOUNT_NOT_FOUND",
            message=f"Account '{account_id}' does not exist"
        )

    # Base conditions
    filters = [Transaction.account_id == account_id]
    if tx_type:
        tx_type_lower = tx_type.lower()
        if tx_type_lower not in ("credit", "debit"):
            raise LedgerException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="INVALID_TRANSACTION_TYPE",
                message=f"Invalid transaction type filter: '{tx_type}'. Must be 'credit' or 'debit'"
            )
        filters.append(Transaction.type == tx_type_lower)

    # Total count query
    count_stmt = select(func.count(Transaction.id)).where(and_(*filters))
    total_records = (await db.execute(count_stmt)).scalar() or 0

    total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
    offset = (page - 1) * limit

    # Query items ordered by created_at DESC (latest-first)
    items_stmt = (
        select(Transaction)
        .where(and_(*filters))
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = (await db.execute(items_stmt)).scalars().all()

    return list(items), total_records, total_pages

async def transfer_money(db: AsyncSession, transfer_in: TransferCreate):
    """
    Executes an atomic money transfer between two accounts.
    Locks both accounts in consistent deterministic order to avoid deadlocks.
    """
    if transfer_in.source_account_id == transfer_in.destination_account_id:
        raise LedgerException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_TRANSFER",
            message="Source and destination accounts must be different"
        )

    # Check duplicate reference on source account
    dup_stmt = select(Transaction).where(
        and_(
            Transaction.account_id == transfer_in.source_account_id,
            Transaction.reference_id == transfer_in.reference_id
        )
    )
    dup = (await db.execute(dup_stmt)).scalar_one_or_none()
    if dup:
        raise LedgerException(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_TRANSFER",
            message=f"Transfer with reference_id '{transfer_in.reference_id}' already executed"
        )

    # Deadlock prevention: sort account IDs alphabetically
    ordered_ids = sorted([transfer_in.source_account_id, transfer_in.destination_account_id])

    # Lock both accounts in deterministic order
    locked_accounts = {}
    for acc_id in ordered_ids:
        acc_stmt = select(Account).where(Account.id == acc_id).with_for_update()
        acc = (await db.execute(acc_stmt)).scalar_one_or_none()
        if not acc:
            raise LedgerException(
                status_code=status.HTTP_404_NOT_FOUND,
                error_code="ACCOUNT_NOT_FOUND",
                message=f"Account '{acc_id}' not found"
            )
        locked_accounts[acc_id] = acc

    source_acc = locked_accounts[transfer_in.source_account_id]
    dest_acc = locked_accounts[transfer_in.destination_account_id]

    amount = Decimal(str(transfer_in.amount))
    if source_acc.balance < amount:
        raise LedgerException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INSUFFICIENT_BALANCE",
            message=f"Source account balance ({source_acc.balance}) is insufficient for transfer amount ({amount})"
        )

    # Atomic balance adjustments
    source_acc.balance -= amount
    dest_acc.balance += amount

    # Create matching ledger transactions
    src_tx = Transaction(
        account_id=source_acc.id,
        type="debit",
        amount=amount,
        description=f"{transfer_in.description} (To: {dest_acc.name})",
        reference_id=transfer_in.reference_id
    )
    dest_tx = Transaction(
        account_id=dest_acc.id,
        type="credit",
        amount=amount,
        description=f"{transfer_in.description} (From: {source_acc.name})",
        reference_id=f"TRF-{transfer_in.reference_id}"
    )

    db.add(src_tx)
    db.add(dest_tx)

    try:
        await db.commit()
        await db.refresh(src_tx)
        await db.refresh(dest_tx)
        await db.refresh(source_acc)
        return {
            "status": "success",
            "message": f"Successfully transferred {amount} from {source_acc.name} to {dest_acc.name}",
            "amount": amount,
            "source_account_id": source_acc.id,
            "destination_account_id": dest_acc.id,
            "source_balance": source_acc.balance,
            "source_transaction_id": src_tx.id,
            "destination_transaction_id": dest_tx.id
        }
    except Exception as e:
        await db.rollback()
        raise LedgerException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="TRANSFER_FAILED",
            message=f"Transfer could not be processed: {str(e)}"
        )
