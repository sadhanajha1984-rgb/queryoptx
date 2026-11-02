"""
SQL Safety and Read-Only Validator
Guarantees that only safe SELECT queries can be analyzed and executed.
"""
import re
from typing import Tuple

FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bLOCK\b",
    r"\bVACUUM\b",
    r"\bCOPY\b"
]

def validate_sql_safety(sql: str) -> Tuple[bool, str]:
    """
    Validates that the provided SQL query is strictly read-only SELECT.
    Returns (is_valid, error_message).
    """
    if not sql or not sql.strip():
        return False, "Query is empty."

    cleaned_sql = sql.strip()

    # Check for multiple statements separated by semicolon (disallow multi-statement injections)
    statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]
    if len(statements) > 1:
        return False, "Multiple SQL statements are not permitted in a single request."

    single_stmt = statements[0]

    # Must start with SELECT or WITH (for CTEs)
    if not (re.match(r"^\s*SELECT\b", single_stmt, re.IGNORECASE) or re.match(r"^\s*WITH\b", single_stmt, re.IGNORECASE)):
        return False, "Only SELECT queries are supported."

    # Check against destructive keywords
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, single_stmt, re.IGNORECASE):
            match = re.search(pattern, single_stmt, re.IGNORECASE).group(0)
            return False, f"Destructive or mutating SQL keyword '{match.upper()}' is strictly prohibited."

    return True, ""
