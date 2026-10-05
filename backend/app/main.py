from __future__ import annotations

import os, re, secrets
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
from pydantic import BaseModel, Field
from backend.app.services.scam_service import analyze_message, training_metrics
from backend.app.services.transaction_anomaly_service import analyze_transaction, warm_model
from backend.app.services.payment_service import validate_payment
from backend.app.services.scheme_service import match_schemes as match_scheme_records
from .services.assistant_service import AssistantService
from .db import database_enabled, database_mode, init_schema
from .services.storage import add_transaction, anomaly_history, contacts as stored_contacts, dashboard as stored_dashboard, profile as stored_profile, safety_alerts as stored_alerts, transactions as stored_transactions, update_profile as stored_update_profile

ROOT = Path(__file__).resolve().parents[2]
def money(value: float) -> str:
    return f'₹{value:,.0f}'

app = FastAPI(title='Sahaay API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

@app.on_event('startup')
def startup():
    init_schema()
    training_metrics()
    warm_model(anomaly_history())

profile = {'id':'u1','name':'Meera Sharma','language':'English','state':'Karnataka','age_group':'25-40','occupation':'Working adult','income_category':'Lower middle income','student_status':'Employed','safety_reminders':True}
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
    {'id':'a1','alert_type':'payment_confirmation','title':'Payment needs your confirmation','detail':'A simulated payment to Ravi is waiting for your review.','severity':'medium','time':'Just now'},
    {'id':'a2','alert_type':'security_recommendation','title':'Keep your OTP private','detail':'Sahaay will never ask for your OTP, PIN, or password.','severity':'low','time':'Today'},
    {'id':'a3','alert_type':'suspicious_message','title':'Suspicious message detected','detail':'A recent message included urgent language and a request for private information.','severity':'high','time':'Yesterday'},
    {'id':'a4','alert_type':'unusual_transaction','title':'Unusual transaction to review','detail':'A simulated payment is outside your usual pattern. Check the recipient before confirming.','severity':'medium','time':'Yesterday'},
]
pending: dict[str, dict[str, Any]] = {}
last_anomaly: dict[str, Any] | None = None
assistant_service = AssistantService()

class AskRequest(BaseModel): message: str = Field(min_length=1, max_length=1000)
class ScamRequest(BaseModel): text: str = Field(min_length=1, max_length=5000)
class PaymentPrepare(BaseModel): contact_id: str; amount: float = Field(gt=0, le=100000)
class PaymentConfirm(BaseModel): confirmation_token: str; anomaly_acknowledged: bool = False
class AnomalyRequest(BaseModel): user_id: str = 'u1'; contact_id: str | None = None; amount: float = Field(gt=0, le=100000); transaction_time: datetime | None = None
class SchemeMatch(BaseModel): state: str='Karnataka'; age_group: str='25-40'; occupation: str='Working adult'; income_category: str='Lower middle income'; student_status: str='Employed'

schemes = [
    {'id':'s1','name':'PM SVANidhi','description':'Working capital support for eligible street vendors.','target_group':'Street vendors','state':'All India','eligibility':'Street vendors identified in the official survey or with a vending certificate.','benefits':'Loans up to ₹10,000 in the first cycle.','required_documents':'Aadhaar, vending certificate or survey record','application_information':'Apply through an official lending institution or the scheme portal.','official_source':'pmsvanidhi.mohua.gov.in'},
    {'id':'s2','name':'PM-KISAN','description':'Income support for eligible landholding farmer families.','target_group':'Farmers','state':'All India','eligibility':'Eligible landholding farmer families as defined by the official scheme rules.','benefits':'₹6,000 per year in three instalments.','required_documents':'Aadhaar, land records, bank account','application_information':'Verify land and beneficiary details through the official portal.','official_source':'pmkisan.gov.in'},
    {'id':'s3','name':'National Scholarship Portal','description':'A starting point for eligible students to discover scholarships.','target_group':'Students','state':'All India','eligibility':'Varies by scholarship and student category; verify each listing.','benefits':'Varies by verified scholarship.','required_documents':'Student ID, income certificate, marksheet','application_information':'Search and apply through the official portal after checking the scheme notice.','official_source':'scholarships.gov.in'},
]

@app.get('/api/health')
def health(): return {'status':'ok','service':'sahaay-api','mode':'simulated','database':database_mode() if database_enabled() else 'unavailable'}

@app.post('/api/voice/transcribe')
async def transcribe_voice(file: UploadFile = File(...), language: str = 'English'):
    supported = {'English', 'Hindi', 'Kannada', 'Telugu'}
    if language not in supported:
        raise HTTPException(400, 'Unsupported voice language')
    if file.content_type not in {'audio/webm', 'audio/ogg', 'audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/x-m4a'}:
        raise HTTPException(415, 'Unsupported audio format. Please record again.')
    audio = await file.read()
    if not audio or len(audio) > 10 * 1024 * 1024:
        raise HTTPException(413, 'Recording is empty or too large. Please try a shorter recording.')
    api_url = os.getenv('MANUS_API_URL')
    api_key = os.getenv('MANUS_API_KEY')
    if not api_url or not api_key:
        raise HTTPException(503, 'Voice transcription is not configured. You can still use Sahaay by typing.')
    prompt = f'Transcribe the user voice to text. The selected language is {language}. Preserve the words and numbers accurately.'
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f'{api_url.rstrip("/")}/v1/audio/transcriptions',
                headers={'Authorization': f'Bearer {api_key}'},
                data={'model': 'whisper-1', 'prompt': prompt},
                files={'file': (file.filename or 'recording.webm', audio, file.content_type)},
            )
        if response.status_code >= 400:
            raise HTTPException(502, 'Voice transcription is temporarily unavailable. Please try again or type your question.')
        payload = response.json()
        text = (payload.get('text') or '').strip()
        if not text:
            raise HTTPException(422, 'Could not understand that recording. Please try again.')
        return {'text': text, 'language': payload.get('language') or language}
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, 'Voice transcription is temporarily unavailable. Please try again or type your question.')
@app.get('/api/profile')
def get_profile(): return stored_profile()
@app.patch('/api/profile')
def patch_profile(data: dict[str, Any]): return stored_update_profile(data)
@app.get('/api/dashboard')
def dashboard(): return stored_dashboard()
@app.get('/api/transactions')
def get_transactions(limit: int=20):
    data = stored_dashboard()
    return {'balance':data['balance'],'income':data['income'],'expenses':data['expenses'],'transactions':stored_transactions(limit)}
@app.get('/api/contacts')
def get_contacts(): return {'contacts':stored_contacts()}

@app.post('/api/ask')
def ask(req: AskRequest):
    text = req.message.lower()
    current = stored_dashboard()
    recent = stored_transactions(4)
    if last_anomaly and any(word in text for word in ['flagged', 'unusual', 'anomaly', 'why was my payment']):
        anomaly = last_anomaly['anomaly']
        amount = last_anomaly['amount']
        if anomaly['is_anomaly']:
            return {'answer':f"This simulated payment of {money(amount)} was flagged because {' '.join(anomaly['reasons'])} Please verify the recipient and amount before continuing.", 'intent':{'name':'transaction_anomaly_explanation'}, 'data':{'anomaly':anomaly}}
        return {'answer':f"This simulated payment of {money(amount)} was within your normal range, so it was not flagged. Review the recipient and amount before confirming.", 'intent':{'name':'transaction_anomaly_explanation'}, 'data':{'anomaly':anomaly}}
    gemini_answer = assistant_service.try_answer(req.message, {'balance': current['balance'], 'income': current['income'], 'expenses': current['expenses'], 'recent_transactions': recent})
    if gemini_answer:
        return {'answer': gemini_answer, 'intent': {'name': 'gemini_explanation'}}
    available_contacts = stored_contacts()
    if any(x in text for x in ['send','pay','transfer']) and any(x in text for x in ['ravi','anita','kiran']):
        recipient = next((c['name'] for c in available_contacts if c['name'].split()[0].lower() in text), 'your contact')
        amount = re.search(r'(?:₹|rs\.?|inr\s*)(\d+(?:\.\d+)?)', text)
        value = f"₹{amount.group(1)}" if amount else 'the amount you choose'
        return {'answer':f'I can help prepare a simulated payment to {recipient} for {value}. I will not send it automatically. Open Payments to review the recipient and confirm the demo transaction yourself.','intent':{'name':'send_money','recipient':recipient,'amount':amount.group(1) if amount else None},'safe_action':'/payments'}
    if 'balance' in text or 'how much do i have' in text or 'account total' in text: return {'answer':f'Your simulated account balance is {money(current["balance"])}. You can review the income, expenses, and recent activity on Transactions.','intent':{'name':'account_balance'},'data':{'balance':current['balance']}}
    if 'spend' in text or 'expense' in text or 'month' in text: return {'answer':f'You have spent {money(current["expenses"])} in the current demo month. I can show the full list in Transactions.','intent':{'name':'spending_summary'},'data':{'expenses':current['expenses']}}
    if 'recent' in text or 'transaction' in text: return {'answer':'Your recent simulated activity includes ' + ', '.join(f'{money(t["amount"])} {"from" if t["direction"]=="income" else "to"} {t["merchant"]}' for t in recent) + '.','intent':{'name':'recent_transactions'},'data':{'transactions':recent}}
    if 'scam' in text or 'message' in text or 'otp' in text or 'pin' in text: return {'answer':'If a message asks for an OTP, PIN, password, urgent payment, or a suspicious link, pause. Do not reply or click. Paste it into Scam Check and verify through an official channel.','intent':{'name':'scam_check','safe_action':'/scam-check'}}
    if 'payment' in text or 'transfer' in text: return {'answer':'A payment is a transfer of money to a recipient. In this demo, Sahaay only prepares the recipient and amount for your review; nothing moves until you explicitly confirm a simulated payment.','intent':{'name':'payment_explanation','safe_action':'/payments'}}
    if 'scheme' in text or 'eligible' in text: return {'answer':'I can help you explore a few sample references based on your profile. Open Government Schemes to compare the target group, documents, benefits, and official source. Always verify current eligibility on the official site.','intent':{'name':'scheme_match','safe_action':'/schemes'}}
    return {'answer':'I can help with spending, transactions, scam messages, payments, safety, and government schemes. Ask me in simple words — for example, “How much did I spend this month?”','intent':{'name':'general_help'}}

@app.post('/api/scam-check')
def scam_check(req: ScamRequest):
    return analyze_message(req.text)

def public_anomaly(result: dict[str, Any]) -> dict[str, Any]:
    return {key: result[key] for key in ('anomaly_level', 'anomaly_score', 'is_anomaly', 'reasons', 'recommended_action')}

@app.post('/api/transaction-anomaly-check')
def transaction_anomaly_check(req: AnomalyRequest):
    if req.user_id != 'u1':
        raise HTTPException(404, 'Simulated user not found')
    contact = next((item for item in stored_contacts() if item['id'] == req.contact_id), None)
    result = analyze_transaction(anomaly_history(), req.amount, req.transaction_time, contact['name'] if contact else None)
    return public_anomaly(result)

@app.post('/api/payments/prepare')
def prepare_payment(req: PaymentPrepare):
    global last_anomaly
    contact = validate_payment(stored_contacts(), req.contact_id, req.amount)
    anomaly = analyze_transaction(anomaly_history(), req.amount, datetime.utcnow(), contact['name'])
    last_anomaly = {'contact': contact, 'amount': req.amount, 'anomaly': anomaly}
    token = secrets.token_urlsafe(18)
    pending[token] = {'contact': contact, 'amount': req.amount, 'anomaly': anomaly}
    return {'contact':contact,'amount':req.amount,'confirmation_token':token,'anomaly':public_anomaly(anomaly),'safety_check':anomaly['recommended_action']}

@app.post('/api/payments/confirm')
def confirm_payment(req: PaymentConfirm):
    item = pending.get(req.confirmation_token)
    if not item:
        raise HTTPException(400, 'Confirmation expired or already used')
    if item['anomaly']['is_anomaly'] and not req.anomaly_acknowledged:
        raise HTTPException(409, 'This unusual simulated payment requires explicit anomaly acknowledgment before confirmation')
    pending.pop(req.confirmation_token, None)
    tx = add_transaction(item['contact']['id'], item['contact']['name'], item['amount'])
    return {'status':'completed','simulated':True,'transaction':tx,'anomaly':public_anomaly(item['anomaly'])}

@app.get('/api/schemes')
def get_schemes(): return {'schemes':schemes,'notice':'Sample references only. Verify current details on the official source.'}
@app.post('/api/schemes/match')
def match_schemes(req: SchemeMatch):
    matches=match_scheme_records(schemes, req.state, req.age_group, req.occupation, req.income_category, req.student_status)
    return {'matches':matches,'profile':req.model_dump()}
@app.get('/api/alerts')
def get_alerts(): return {'alerts':stored_alerts()}

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
