# Sahaay MVP outcomes

## 1. Accessible navigation shell and Home experience
- The application is a clean, modern, mobile-first interface designed especially for users with limited digital literacy.
- The interface uses large buttons, large readable text, clear icons, simple language, high contrast, plenty of spacing, clear navigation, simple cards, and friendly but professional design.
- Proper navigation reaches Home, Ask Sahaay, Scam Check, Payments, Transactions, Government Schemes, Safety Alerts, and Profile.
- Home prominently shows Sahaay branding, a short explanation of what Sahaay does, a large Ask Sahaay / Tap to Speak area, quick actions for Scam Check, Payments, Transactions and Government Schemes, recent activity, and safety alerts if applicable.
- Tap to Speak is present as a future multilingual voice placeholder and does not pretend that voice functionality is implemented.
- The UI does not copy the branding or exact UI of PhonePe, Google Pay, Paytm, or another existing banking/payment application.

## 2. Ask Sahaay assistant and safe action boundary
- Ask Sahaay is the central feature and provides a basic text-based assistant that understands questions related to financial transactions, spending, scam messages, payments, government schemes, and basic financial safety.
- The assistant provides simple, understandable responses using simulated financial data for transaction-related questions.
- Example questions such as “How much did I spend this month?”, “Show me my recent transactions.”, “Is this message a scam?”, “What government schemes am I eligible for?”, and “Send ₹500 to Ravi.” have useful responses or a safe next step.
- The assistant must not directly execute financial actions.
- The architecture follows user -> AI intent understanding -> structured request -> backend validation -> safety checks -> user confirmation -> simulated action -> result.
- Gemini integration is isolated behind an adapter and can be configured later; the MVP remains functional with deterministic fallback responses when no Gemini key is available.

## 3. Simulated financial data and transactions
- Realistic mock users, accounts, contacts, and transaction data are available.
- The data includes account balance, recent transactions, income, expenses, monthly spending summary, transaction categories, and recipient/contact information.
- Backend APIs retrieve the simulated financial information and connect it to Transactions and Ask Sahaay.
- The data is structured so anomaly detection can be added later.
- The Transactions screen shows balance and monthly income/expense summaries, categories, and recent transaction records.

## 4. Scam Check analysis
- Scam Check lets a user paste a suspicious SMS/message or enter suspicious financial text and submit it for analysis.
- The result includes risk level, risk score, reasons, and a safety recommendation.
- The initial implementation uses sample/mock rule-based detection and has a modular boundary for a future Scikit-learn TF-IDF + Logistic Regression model.
- The detection architecture can recognize requests for OTP/PIN/password, suspicious links, urgent payment requests, threats such as account blocking, prize/reward scams, impersonation, and requests for sensitive financial information.

## 5. Safe simulated payments
- The user can select a mock recipient, enter an amount, review payment details, explicitly confirm the payment, and complete a simulated transaction.
- A request such as “Send ₹500 to Ravi” results in a review showing Recipient: Ravi and Amount: ₹500, followed by “Confirm payment?”.
- Only after explicit user confirmation is the simulated transaction completed.
- The system never executes a real financial transaction, never requests real banking credentials or real UPI PINs, and clearly labels the flow as simulated/demo.
- Backend validation rejects invalid recipients/amounts and the assistant response cannot call payment completion directly.

## 6. Government schemes matching
- A structured sample dataset contains scheme name, description, target group, state, eligibility, benefits, required documents, application information, and official source/reference.
- A basic profile-based matching system accepts age group, occupation, student/employment status, state, and income category.
- The system returns potentially relevant schemes using deterministic rules where possible.
- The AI does not invent government schemes or eligibility criteria; verified/reference fields are shown as structured sample content.

## 7. Safety Alerts and Profile
- Safety Alerts displays suspicious message detected, unusual transaction detected, payment requires confirmation, and security recommendation alert types.
- The alert structure allows future anomaly detection to generate alerts automatically.
- Profile contains user name, preferred language, basic profile information, safety preferences, a voice settings placeholder, and privacy/security section.
- Future language options include English, Hindi, Kannada, and Telugu; actual multilingual voice functionality is not implemented in this MVP.

## 8. Full-stack architecture and delivery documentation
- The frontend is React with Tailwind CSS and the backend is modular FastAPI with PostgreSQL-ready models/schema for Users, Accounts, Transactions, Contacts, Government Schemes, and Safety Alerts.
- Frontend and backend are clearly separated, with modular assistant, scam, payment, scheme, alert, and data-access services.
- API endpoints exist for Ask Sahaay, transactions, account balance/dashboard data, scam checking, contacts, simulated payments, government schemes, safety alerts, and user profile.
- The application runs in managed Preview with FastAPI serving the built React app and `/api/health`, while development instructions support separate frontend/backend processes.
- README documentation explains dependency installation, environment variables, Gemini configuration, PostgreSQL setup, starting FastAPI, starting React/Vite, the project folder structure, important files, and the simulated-only security boundary.
- No real banking integration, real money movement, advanced multilingual voice, advanced ML training, or complex RAG is attempted in this MVP.
