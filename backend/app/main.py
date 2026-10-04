from __future__ import annotations

import os, re, secrets
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from backend.app.services.scam_service import analyze_message
from backend.app.services.assistant_service import AssistantService

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title='Sahaay API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

profile = {'id':'u1','name':'Meera Sharma','language':'English','state':'Karnataka','age_group':'25-40','occupation':'Working adult','income_category':'Lower middle income','student_status':'Employed'}
contacts = [
    {'id':'c1','name':'Ravi Kumar','relation':'Brother','initials':'RK'},
    {'id':'c2','name':'Anita Sharma','relation':'Neighbour','initials':'AS'},
    {'id':'c3','name':'Kiran Stores','relation':'Local shop','initials':'KS'},
]
transactions: list[dict[str, Any]] = [
    {'id':'t1','merchant':'Ravi Kumar','category':'Family','amount':500,'direction':'expense','date':'Today, 10:42 AM','note':'Simulated payment'},
    {'id':'t2','merchant':'Fresh Basket','category':'Groceries','amount':860,'direction':'expense','date':'Yesterday, 6:15 PM','note':'Monthly essentials'},
    {'id':'t3','merchant':'Asha Textiles','category':'Income','amount':18500,'direction':'income','date':'01 Oct 2026','note':'Simulated salary credit'},
    {'id':'t4','merchant':'Metro Recharge','category':'Bills','amount':299,'direction':'expense','date':'29 Sep 2026','note':'Mobile recharge'},
]
alerts = [
    {'id':'a1','title':'Payment needs your confirmation','detail':'A simulated payment to Ravi is waiting for your review.','severity':'medium','time':'Just now'},
    {'id':'a2','title':'Keep your OTP private','detail':'Sahaay will never ask for your OTP, PIN, or password.','severity':'low','time':'Today'},
    {'id':'a3','title':'Suspicious message detected','detail':'A recent message included urgent language and a request for private information.','severity':'high','time':'Yesterday'},
    {'id':'a4','title':'Unusual transaction to review','detail':'A simulated payment is outside your usual pattern. Check the recipient before confirming.','severity':'medium','time':'Yesterday'},
]
pending: dict[str, dict[str, Any]] = {}
assistant_service = AssistantService()

class AskRequest(BaseModel): message: str = Field(min_length=1, max_length=1000)
class ScamRequest(BaseModel): text: str = Field(min_length=1, max_length=5000)
class PaymentPrepare(BaseModel): contact_id: str; amount: float = Field(gt=0, le=100000)
class PaymentConfirm(BaseModel): confirmation_token: str
class SchemeMatch(BaseModel): state: str='Karnataka'; age_group: str='25-40'; occupation: str='Working adult'; income_category: str='Lower middle income'; student_status: str='Employed'

schemes = [
    {'id':'s1','name':'PM SVANidhi','description':'Working capital support for eligible street vendors.','target_group':'Street vendors','state':'All India','eligibility':'Street vendors identified in the official survey or with a vending certificate.','benefits':'Loans up to ₹10,000 in the first cycle.','required_documents':'Aadhaar, vending certificate or survey record','application_information':'Apply through an official lending institution or the scheme portal.','official_source':'pmsvanidhi.mohua.gov.in'},
    {'id':'s2','name':'PM-KISAN','description':'Income support for eligible landholding farmer families.','target_group':'Farmers','state':'All India','eligibility':'Eligible landholding farmer families as defined by the official scheme rules.','benefits':'₹6,000 per year in three instalments.','required_documents':'Aadhaar, land records, bank account','application_information':'Verify land and beneficiary details through the official portal.','official_source':'pmkisan.gov.in'},
    {'id':'s3','name':'National Scholarship Portal','description':'A starting point for eligible students to discover scholarships.','target_group':'Students','state':'All India','eligibility':'Varies by scholarship and student category; verify each listing.','benefits':'Varies by verified scholarship.','required_documents':'Student ID, income certificate, marksheet','application_information':'Search and apply through the official portal after checking the scheme notice.','official_source':'scholarships.gov.in'},
]

@app.get('/api/health')
def health(): return {'status':'ok','service':'sahaay-api','mode':'simulated'}
@app.get('/api/profile')
def get_profile(): return profile
@app.patch('/api/profile')
def patch_profile(data: dict[str, Any]): profile.update({k:v for k,v in data.items() if k in profile}); return profile
@app.get('/api/dashboard')
def dashboard(): return {'balance':24850,'income':18500,'expenses':sum(t['amount'] for t in transactions if t['direction']=='expense'),'safe_to_spend':12640,'transactions':transactions[:4],'alerts':alerts}
@app.get('/api/transactions')
def get_transactions(limit: int=20): return {'balance':24850,'transactions':transactions[:max(1,min(limit,100))]}
@app.get('/api/contacts')
def get_contacts(): return {'contacts':contacts}

@app.post('/api/ask')
def ask(req: AskRequest):
    text = req.message.lower()
    gemini_answer = assistant_service.try_answer(req.message, {'balance': 24850, 'recent_transactions': transactions[:4]})
    if gemini_answer:
        return {'answer': gemini_answer, 'intent': {'name': 'gemini_explanation'}}
    if any(x in text for x in ['send','pay','transfer']) and any(x in text for x in ['ravi','anita','kiran']):
        recipient = next((c['name'] for c in contacts if c['name'].split()[0].lower() in text), 'your contact')
        amount = re.search(r'(?:₹|rs\.?|inr\s*)(\d+(?:\.\d+)?)', text)
        value = f"₹{amount.group(1)}" if amount else 'the amount you choose'
        return {'answer':f'I can help prepare a simulated payment to {recipient} for {value}. I will not send it automatically. Open Payments to review the recipient and confirm the demo transaction yourself.','intent':{'name':'send_money','recipient':recipient,'amount':amount.group(1) if amount else None},'safe_action':'/payments'}
    if 'spend' in text or 'expense' in text or 'month' in text: return {'answer':'You have spent ₹1,659 in the current demo month. That includes groceries, a mobile recharge, and a simulated family payment. I can show the full list in Transactions.','intent':{'name':'spending_summary'}}
    if 'recent' in text or 'transaction' in text: return {'answer':'Your recent simulated activity includes ₹500 to Ravi Kumar, ₹860 at Fresh Basket, ₹18,500 income from Asha Textiles, and ₹299 for Metro Recharge.','intent':{'name':'recent_transactions'}}
    if 'scam' in text or 'message' in text or 'otp' in text or 'pin' in text: return {'answer':'If a message asks for an OTP, PIN, password, urgent payment, or a suspicious link, pause. Do not reply or click. Paste it into Scam Check and verify through an official channel.','intent':{'name':'scam_check','safe_action':'/scam-check'}}
    if 'scheme' in text or 'eligible' in text: return {'answer':'I can help you explore a few sample references based on your profile. Open Government Schemes to compare the target group, documents, benefits, and official source. Always verify current eligibility on the official site.','intent':{'name':'scheme_match','safe_action':'/schemes'}}
    return {'answer':'I can help with spending, transactions, scam messages, payments, safety, and government schemes. Ask me in simple words — for example, “How much did I spend this month?”','intent':{'name':'general_help'}}

@app.post('/api/scam-check')
def scam_check(req: ScamRequest):
    return analyze_message(req.text)

@app.post('/api/payments/prepare')
def prepare_payment(req: PaymentPrepare):
    contact=next((c for c in contacts if c['id']==req.contact_id),None)
    if not contact: raise HTTPException(404,'Recipient not found')
    token=secrets.token_urlsafe(18); pending[token]={'contact':contact,'amount':req.amount}; return {'contact':contact,'amount':req.amount,'confirmation_token':token,'safety_check':'Recipient and amount validated. Explicit confirmation required.'}
@app.post('/api/payments/confirm')
def confirm_payment(req: PaymentConfirm):
    item=pending.pop(req.confirmation_token,None)
    if not item: raise HTTPException(400,'Confirmation expired or already used')
    tx={'id':f"t{len(transactions)+1}",'merchant':item['contact']['name'],'category':'Family','amount':item['amount'],'direction':'expense','date':'Just now','note':'Simulated payment'}; transactions.insert(0,tx); return {'status':'completed','simulated':True,'transaction':tx}

@app.get('/api/schemes')
def get_schemes(): return {'schemes':schemes,'notice':'Sample references only. Verify current details on the official source.'}
@app.post('/api/schemes/match')
def match_schemes(req: SchemeMatch):
    occupation=req.occupation.lower(); matches=schemes
    if 'student' in occupation: matches=[schemes[2]]
    elif 'vendor' in occupation: matches=[schemes[0]]
    elif 'farmer' in occupation: matches=[schemes[1]]
    return {'matches':matches,'profile':req.model_dump()}
@app.get('/api/alerts')
def get_alerts(): return {'alerts':alerts}

frontend = ROOT / 'frontend' / 'dist'
if frontend.exists():
    app.mount('/assets', StaticFiles(directory=frontend/'assets'), name='assets')
    @app.get('/manus-routes.json')
    def route_manifest():
        return FileResponse(ROOT / 'public' / 'manus-routes.json', media_type='application/json')

    @app.get('/{path:path}')
    def serve_spa(path: str):
        requested=frontend/path
        return FileResponse(requested if requested.exists() and requested.is_file() else frontend/'index.html')
