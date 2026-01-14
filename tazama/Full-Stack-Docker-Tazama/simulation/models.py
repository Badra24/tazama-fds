from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GroupHeader(BaseModel):
    MsgId: str
    CreDtTm: datetime
    NbOfTx: int
    InitgPty: dict  # Simplified to a dict for this simulation

class StartAmount(BaseModel):
    Amount: float
    Ccy: str

class Account(BaseModel):
    Iban: str

class Agent(BaseModel):
    Bic: str

class Party(BaseModel):
    Nm: str
    PstlAdr: Optional[dict] = None

class CreditTransferTransactionInformation(BaseModel):
    PmtId: str
    IntrBkSttlmAmt: StartAmount
    Dbtr: Party
    DbtrAcct: Account
    DbtrAgt: Agent
    CdtrAgt: Agent
    Cdtr: Party
    CdtrAcct: Account

class Pacs008Message(BaseModel):
    GrpHdr: GroupHeader
    CdtTrfTxInf: List[CreditTransferTransactionInformation]
