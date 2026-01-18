from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.db import Base, utcnow

class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, unique=True, index=True, nullable=False)
    account_id = Column(String, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)

class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, unique=True, index=True, nullable=False)
    provider = Column(String, default="mock-provider")
    access_token_enc = Column(Text, nullable=False)
    refresh_token_enc = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, index=True, nullable=False)
    provider_txn_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)  # cents
    currency = Column(String, default="USD")
    description = Column(String, nullable=True)
    posted_at = Column(DateTime, nullable=False)
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('account_id', 'provider_txn_id', name='uq_account_provider_txn'),
    )

class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, unique=True, nullable=False)
    cursor = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
