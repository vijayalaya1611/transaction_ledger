from enum import Enum
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"

# ----------------- Account Schemas -----------------

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Account holder name")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Account name cannot be empty or blank")
        return trimmed

class AccountResponse(BaseModel):
    id: str
    name: str
    balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AccountBalanceResponse(BaseModel):
    account_id: str
    balance: Decimal

# ----------------- Transaction Schemas -----------------

class TransactionCreate(BaseModel):
    account_id: str = Field(..., description="ID of the target account")
    type: TransactionType = Field(..., description="Type of transaction: credit or debit")
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Transaction amount must be strictly greater than 0")
    description: Optional[str] = Field(None, max_length=500, description="Optional transaction description")
    reference_id: str = Field(..., min_length=1, max_length=255, description="Unique reference ID within the account")

    @field_validator("reference_id")
    @classmethod
    def reference_id_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("reference_id cannot be empty or whitespace")
        return trimmed

class TransactionResponse(BaseModel):
    id: str
    account_id: str
    type: str
    amount: Decimal
    description: Optional[str]
    reference_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionPaginationResponse(BaseModel):
    current_page: int
    page_size: int
    total_records: int
    total_pages: int
    transactions: List[TransactionResponse]

# ----------------- Bonus: Money Transfer Schemas -----------------

class TransferCreate(BaseModel):
    source_account_id: str = Field(..., description="Source account ID to debit from")
    destination_account_id: str = Field(..., description="Destination account ID to credit to")
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Amount to transfer")
    description: Optional[str] = Field("Fund Transfer", max_length=500)
    reference_id: str = Field(..., min_length=1, max_length=255, description="Unique reference ID")

    @field_validator("reference_id")
    @classmethod
    def validate_reference_id(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("reference_id cannot be blank")
        return trimmed

class TransferResponse(BaseModel):
    status: str
    message: str
    amount: Decimal
    source_account_id: str
    destination_account_id: str
    source_balance: Decimal
    source_transaction_id: str
    destination_transaction_id: str
