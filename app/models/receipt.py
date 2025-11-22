"""Receipt extraction Pydantic schemas for OCR validation."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from enum import StrEnum
from datetime import datetime, timezone


class ReceiptDocumentType(StrEnum):
    RECEIPT = "receipt"
    TRANSFER = "transfer"


class ReceiptItem(BaseModel):
    """Schema for individual receipt item.

    Represents a single item from a receipt with description and amount.
    """

    description: str = Field(..., description="Item description or name")
    amount: float = Field(..., gt=0, description="Item price amount")
    count: int = Field(..., gt=0, description="Item count")


class ReceiptExtraction(BaseModel):
    """Schema for complete receipt extraction from OCR.

    Contains all extracted information from a receipt including merchant,
    date, totals, tip, and itemized breakdown.
    """

    merchant: str = Field(..., description="Merchant or restaurant name")
    receipt_date: date = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).replace(tzinfo=None).date(),
        description="Receipt date in YYYY-MM-DD format",
        alias="date",
    )
    total_amount: float = Field(..., gt=0, description="Total amount of the receipt")
    tip: float = Field(
        default=0.0,
        ge=0,
        description="Tip amount (defaults to 0.0 if not detected)",
    )
    items: list[ReceiptItem] = Field(..., min_length=1, description="List of items on the receipt")


class TransferExtraction(BaseModel):
    """Schema for transfer extraction from OCR.

    Contains extracted information from a bank transfer or payment transfer document.
    """

    recipient: str = Field(..., description="Recipient name or account identifier")
    amount: float = Field(..., gt=0, description="Transfer amount")
    description: str | None = Field(default=None, description="Optional transfer description or reference")


class DocumentExtraction(BaseModel):
    """Unified schema for document extraction (receipt or transfer).

    Contains the document type and the corresponding extracted data.
    """

    document_type: ReceiptDocumentType = Field(..., description="Type of document: 'receipt' or 'transfer'")
    receipt: ReceiptExtraction | None = Field(default=None, description="Receipt data if document_type is 'receipt'")
    transfer: TransferExtraction | None = Field(
        default=None, description="Transfer data if document_type is 'transfer'"
    )
