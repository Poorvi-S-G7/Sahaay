import re

RULES = [
    (r'otp|one[- ]time password|pin|password', 'This message asks for an OTP, PIN, or password.'),
    (r'https?://|www\\.', 'It includes a link that should be verified before opening.'),
    (r'urgent|immediately|act now|today', 'It creates pressure to act quickly.'),
    (r'block|suspend|close your account', 'It threatens account blocking or suspension.'),
    (r'prize|reward|lottery|won', 'It uses a prize or reward claim.'),
    (r'verify your (account|identity)|kyc', 'It asks for sensitive account or identity details.'),
]

def analyze_message(text: str) -> dict:
    lowered = text.lower()
    reasons = [reason for pattern, reason in RULES if re.search(pattern, lowered)]
    score = min(98, max(8, len(reasons) * 18 + (20 if 'http' in lowered else 0)))
    level = 'High' if score >= 60 else ('Medium' if score >= 30 else 'Low')
    if not reasons:
        reasons = ['No obvious scam patterns found. Still verify the sender through an official channel.']
    recommendation = ('Do not click links or share any code. Contact the organisation using a phone number or website you already trust.'
                      if score >= 30 else 'Pause and verify the sender through an official channel. Never share private codes.')
    return {'risk_level': level, 'score': score, 'reasons': reasons, 'recommendation': recommendation}
