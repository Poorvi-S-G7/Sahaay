from __future__ import annotations

from datetime import datetime
from typing import Any
from sqlalchemy import select
from ..db import SessionLocal
from ..models import Account, Contact, SafetyAlert, Transaction, User


def _session():
    if SessionLocal is None:
        raise RuntimeError('Database session is not configured')
    return SessionLocal()


def seed_demo_data() -> None:
    with _session() as db:
        if db.scalar(select(User).where(User.id == 'u1')):
            return
        db.add(User(id='u1', name='Meera Sharma', language='English', state='Karnataka', age_group='25-40', occupation='Working adult', income_category='Lower middle income', student_status='Employed', safety_reminders=True))
        db.flush()
        db.add(Account(id='ac1', user_id='u1', label='Demo account', balance=24850, currency='INR'))
        db.add_all([
            Contact(id='c1', user_id='u1', name='Ravi Kumar', relation='Brother'),
            Contact(id='c2', user_id='u1', name='Anita Sharma', relation='Neighbour'),
            Contact(id='c3', user_id='u1', name='Kiran Stores', relation='Local shop'),
        ])
        db.add_all([
            Transaction(id='t1', account_id='ac1', contact_id='c1', merchant='Ravi Kumar', category='Family', amount=500, direction='expense', note='Simulated payment', created_at=datetime(2026,10,4,10,42)),
            Transaction(id='t2', account_id='ac1', merchant='Fresh Basket', category='Groceries', amount=860, direction='expense', note='Monthly essentials', created_at=datetime(2026,10,3,18,15)),
            Transaction(id='t3', account_id='ac1', merchant='Asha Textiles', category='Income', amount=18500, direction='income', note='Simulated salary credit', created_at=datetime(2026,10,1,9,0)),
            Transaction(id='t4', account_id='ac1', merchant='Metro Recharge', category='Bills', amount=299, direction='expense', note='Mobile recharge', created_at=datetime(2026,9,29,12,0)),
        ])
        db.add_all([
            SafetyAlert(id='a1', user_id='u1', alert_type='payment_confirmation', title='Payment needs your confirmation', detail='A simulated payment to Ravi is waiting for your review.', severity='medium', time='Just now'),
            SafetyAlert(id='a2', user_id='u1', alert_type='security_recommendation', title='Keep your OTP private', detail='Sahaay will never ask for your OTP, PIN, or password.', severity='low', time='Today'),
            SafetyAlert(id='a3', user_id='u1', alert_type='suspicious_message', title='Suspicious message detected', detail='A recent message included urgent language and a request for private information.', severity='high', time='Yesterday'),
            SafetyAlert(id='a4', user_id='u1', alert_type='unusual_transaction', title='Unusual transaction to review', detail='A simulated payment is outside your usual pattern. Check the recipient before confirming.', severity='medium', time='Yesterday'),
        ])
        db.commit()


def profile() -> dict[str, Any]:
    with _session() as db:
        user = db.get(User, 'u1')
        return {'id':user.id,'name':user.name,'language':user.language,'state':user.state,'age_group':user.age_group,'occupation':user.occupation,'income_category':user.income_category,'student_status':user.student_status,'safety_reminders':user.safety_reminders}


def update_profile(data: dict[str, Any]) -> dict[str, Any]:
    with _session() as db:
        user = db.get(User, 'u1')
        allowed = {'name','language','state','age_group','occupation','income_category','student_status','safety_reminders'}
        for key, value in data.items():
            if key in allowed:
                setattr(user, key, value)
        db.commit()
    return profile()


def contacts() -> list[dict[str, Any]]:
    with _session() as db:
        rows = db.scalars(select(Contact).where(Contact.user_id == 'u1').order_by(Contact.name)).all()
        return [{'id':r.id,'name':r.name,'relation':r.relation,'initials':''.join(p[0] for p in r.name.split()[:2])} for r in rows]


def transactions(limit: int = 20) -> list[dict[str, Any]]:
    with _session() as db:
        rows = db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(max(1,min(limit,100)))).all()
        return [{'id':r.id,'merchant':r.merchant,'category':r.category,'amount':r.amount,'direction':r.direction,'date':r.created_at.strftime('%d %b %Y, %I:%M %p'),'note':r.note} for r in rows]


def anomaly_history() -> list[dict[str, Any]]:
    with _session() as db:
        rows = db.scalars(select(Transaction).order_by(Transaction.created_at.asc())).all()
        return [{'id':r.id,'merchant':r.merchant,'amount':r.amount,'direction':r.direction,'created_at':r.created_at} for r in rows]


def dashboard() -> dict[str, Any]:
    with _session() as db:
        rows = db.scalars(select(Transaction)).all()
        balance = db.get(Account, 'ac1').balance
        income = sum(r.amount for r in rows if r.direction == 'income')
        expenses = sum(r.amount for r in rows if r.direction == 'expense')
        alerts = safety_alerts()
    return {'balance':balance,'income':income,'expenses':expenses,'safe_to_spend':max(0,12640 - max(0, expenses - 1659)),'transactions':transactions(4),'alerts':alerts}


def add_transaction(contact_id: str, merchant: str, amount: float) -> dict[str, Any]:
    with _session() as db:
        count = len(db.scalars(select(Transaction)).all())
        row = Transaction(id=f't{count+1}', account_id='ac1', contact_id=contact_id, merchant=merchant, category='Family', amount=amount, direction='expense', note='Simulated payment', created_at=datetime.utcnow())
        db.add(row); db.commit(); db.refresh(row)
        return {'id':row.id,'merchant':row.merchant,'category':row.category,'amount':row.amount,'direction':row.direction,'date':'Just now','note':row.note}


def safety_alerts() -> list[dict[str, Any]]:
    with _session() as db:
        rows = db.scalars(select(SafetyAlert).where(SafetyAlert.user_id == 'u1').order_by(SafetyAlert.created_at.desc())).all()
        return [{'id':r.id,'alert_type':r.alert_type,'title':r.title,'detail':r.detail,'severity':r.severity,'time':getattr(r,'time','Today')} for r in rows]
