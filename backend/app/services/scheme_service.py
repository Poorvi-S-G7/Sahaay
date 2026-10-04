from typing import Any

def match_schemes(schemes: list[dict[str, Any]], state: str, age_group: str, occupation: str, income_category: str, student_status: str) -> list[dict[str, Any]]:
    occupation = occupation.lower(); status = student_status.lower(); matches = schemes[:]
    if 'student' in occupation or 'student' in status:
        matches = [schemes[2]]
    elif 'vendor' in occupation:
        matches = [schemes[0]]
    elif 'farmer' in occupation:
        matches = [schemes[1]]
    elif income_category.lower() == 'high' and age_group in {'18-24', '25-40'}:
        matches = [schemes[0]]
    if state not in {'All states', 'Karnataka', 'Maharashtra', 'Telangana'}:
        matches = []
    return matches
