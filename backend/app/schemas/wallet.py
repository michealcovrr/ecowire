from pydantic import BaseModel, model_validator


class SendMoneyRequest(BaseModel):
    recipient_id: str
    amount_naira: float
    narration: str = "EcoNet transfer"
    amount_kobo: int = 0

    @model_validator(mode="after")
    def compute_kobo(self):
        self.amount_kobo = int(self.amount_naira * 100)
        return self


class LookupRequest(BaseModel):
    account_number: str
    bank_code: str


class CashInRequest(BaseModel):
    user_id: str
    amount_naira: float
    agent_id: str
    amount_kobo: int = 0

    @model_validator(mode="after")
    def compute_kobo(self):
        self.amount_kobo = int(self.amount_naira * 100)
        return self


class CashOutRequest(BaseModel):
    user_id: str
    amount_naira: float
    agent_id: str
    destination_account: str | None = None
    destination_bank_code: str | None = None
    amount_kobo: int = 0

    @model_validator(mode="after")
    def compute_kobo(self):
        self.amount_kobo = int(self.amount_naira * 100)
        return self


class TransactionResponse(BaseModel):
    transaction_id: str
    type: str
    amount_kobo: int
    amount_naira: float
    status: str
    squad_reference: str | None
    tagged_as: str | None
    timestamp: str
