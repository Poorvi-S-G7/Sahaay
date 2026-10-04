"""Small, clearly labeled demo corpus for the Sahaay scam classifier.

This is simulated training data only. It is intentionally small so the MVP can
train quickly; production-quality performance would require a reviewed corpus.
"""

TRAINING_DATA = [
    # Scam / fraud examples
    {"label": 1, "text": "Urgent your bank account will be blocked today share your OTP to keep it active"},
    {"label": 1, "text": "Your KYC has expired update your PAN and password at this link immediately"},
    {"label": 1, "text": "Congratulations you won a cash prize send your PIN to claim the reward"},
    {"label": 1, "text": "Official income tax refund is waiting click the link and enter your bank details"},
    {"label": 1, "text": "Customer care needs your one time password to cancel the payment right now"},
    {"label": 1, "text": "Act now your card will be suspended verify your CVV at http://secure-update.example"},
    {"label": 1, "text": "Police notice your account is linked to fraud send money immediately to avoid arrest"},
    {"label": 1, "text": "You have won a lottery reward pay a small fee and share your password"},
    {"label": 1, "text": "Bank manager here send your account number PIN and OTP for urgent verification"},
    {"label": 1, "text": "KYC update required today click www.fake-bank.example or your account will close"},
    {"label": 1, "text": "Your wallet has received a prize claim it by entering your card number and CVV"},
    {"label": 1, "text": "Refund team requests your UPI PIN and password to release your money"},
    {"label": 1, "text": "Final warning immediately transfer money to this safe account or lose access"},
    {"label": 1, "text": "Government subsidy approved share your bank details and OTP to receive it"},
    {"label": 1, "text": "Your parcel is held pay now through this link and provide your card details"},
    {"label": 1, "text": "Support team detected suspicious activity verify identity with OTP at this URL"},
    # Legitimate examples
    {"label": 0, "text": "Your bank account was debited by 500 rupees at Ravi Kumar on 04 October"},
    {"label": 0, "text": "Payment of 860 rupees to Fresh Basket was successful from your account"},
    {"label": 0, "text": "Your salary credit of 18500 rupees has been received in your account"},
    {"label": 0, "text": "Your available balance is 24850 rupees as of 04 October"},
    {"label": 0, "text": "Your mobile recharge payment of 299 rupees is confirmed"},
    {"label": 0, "text": "Statement ready: view your monthly account activity in the official banking app"},
    {"label": 0, "text": "Your scheduled bill payment was completed successfully"},
    {"label": 0, "text": "A new transaction notification is available in your bank app"},
    {"label": 0, "text": "Your payment to Kiran Stores for 123 rupees is confirmed"},
    {"label": 0, "text": "Thank you for using our service your receipt is available in the app"},
    {"label": 0, "text": "Your account statement for September is ready to download from the official website"},
    {"label": 0, "text": "The bank branch will be closed on Sunday and reopen Monday morning"},
    {"label": 0, "text": "Your debit card payment was declined please contact the bank using the number on your card"},
    {"label": 0, "text": "You changed your notification preference successfully in the banking app"},
    {"label": 0, "text": "Your recurring payment is scheduled for tomorrow"},
    {"label": 0, "text": "Your account balance notification is ready in the secure bank application"},
]
