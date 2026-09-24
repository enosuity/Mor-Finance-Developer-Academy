"""
Payment callback schema — sandbox/test-mode subscription confirmation.
"""
from typing import Union
from pydantic import BaseModel


class PaymentCallback(BaseModel):
    telegramHandle: str
    chosenCountryNode: str
    paymentAmount: Union[float, str]
    transactionReference: str
