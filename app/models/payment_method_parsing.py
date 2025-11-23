"""Payment method parsing models for structured outputs."""

from pydantic import BaseModel, Field


class PaymentMethodInfo(BaseModel):
    """Schema for payment method information extraction.
    
    Extracts bank name and description from user's payment method message.
    """
    
    bank_name: str = Field(
        ...,
        description="Name of the bank or payment method (e.g., 'Banco de Chile', 'Yape', 'Plin')"
    )
    description: str = Field(
        ...,
        description="Full payment method details including name, RUT, account type, account number, email, etc. Keep the original format and all information provided by the user."
    )
    is_payment_method: bool = Field(
        default=True,
        description="Whether this message contains payment method information (true) or something else (false)"
    )

