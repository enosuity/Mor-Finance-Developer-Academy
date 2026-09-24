"""
Leaderboard schema — testnet activity submissions ranked by distinct transaction count.
"""
from pydantic import BaseModel


class LeaderboardSubmission(BaseModel):
    telegram: str
    chain: str
    txHash: str
