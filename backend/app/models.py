from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(32), default='English')
    state: Mapped[str] = mapped_column(String(80), default='Karnataka')
    age_group: Mapped[str] = mapped_column(String(40), default='25-40')
    occupation: Mapped[str] = mapped_column(String(80), default='Working adult')
    income_category: Mapped[str] = mapped_column(String(80), default='Lower middle income')

class Account(Base):
    __tablename__ = 'accounts'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    label: Mapped[str] = mapped_column(String(80))
    balance: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default='INR')

class Contact(Base):
    __tablename__ = 'contacts'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(120))
    relation: Mapped[str] = mapped_column(String(80))

class Transaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey('accounts.id'))
    contact_id: Mapped[str | None] = mapped_column(ForeignKey('contacts.id'), nullable=True)
    merchant: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80))
    amount: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(16))
    note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class GovernmentScheme(Base):
    __tablename__ = 'government_schemes'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    target_group: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(80))
    eligibility: Mapped[str] = mapped_column(Text)
    benefits: Mapped[str] = mapped_column(Text)
    required_documents: Mapped[str] = mapped_column(Text)
    application_information: Mapped[str] = mapped_column(Text)
    official_source: Mapped[str] = mapped_column(String(240))

class SafetyAlert(Base):
    __tablename__ = 'safety_alerts'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    alert_type: Mapped[str] = mapped_column(String(40), default='security_recommendation')
    title: Mapped[str] = mapped_column(String(160))
    detail: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
