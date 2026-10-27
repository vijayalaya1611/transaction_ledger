import uuid
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
    CheckConstraint,
    Uuid
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    # Native UUID support for PostgreSQL while seamlessly accepting Python string UUIDs
    id = Column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    transactions = relationship("Transaction", back_populates="account", order_by="desc(Transaction.created_at)")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="chk_positive_balance"),
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    account_id = Column(Uuid(as_uuid=False), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # 'credit' or 'debit'
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    account = relationship("Account", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("type IN ('credit', 'debit')", name="chk_transaction_type"),
        CheckConstraint("amount > 0", name="chk_positive_amount"),
        # Enforce that reference_id must be unique for the SAME account
        UniqueConstraint("account_id", "reference_id", name="uq_account_reference"),
        # Optimized sorting index for transaction history
        Index("idx_transactions_account_created", "account_id", "created_at"),
    )
