"""
SQL Normalization & Fingerprinting Module
Converts raw SQL statements into parameterized structural templates for cache reuse.
"""
import hashlib
import re

class QueryNormalizer:
    """
    Strips comments, normalizes whitespace, and masks literal constants (numbers, strings)
    to generate structural query fingerprints.
    """

    @classmethod
    def normalize_and_fingerprint(cls, sql: str) -> tuple[str, str]:
        """
        Returns (normalized_sql_template, sha256_fingerprint).
        """
        # 1. Remove comments
        cleaned = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

        # 2. Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 3. Replace single-quoted string literals with '?'
        template = re.sub(r"'[^']*'", "'?'", cleaned)

        # 4. Replace numeric constants with '?'
        template = re.sub(r"\b\d+(\.\d+)?\b", "?", template)

        # 5. Convert to lower case for case-insensitivity
        template_lower = template.lower()

        # 6. Generate deterministic SHA256 hash
        fingerprint = hashlib.sha256(template_lower.encode("utf-8")).hexdigest()[:16]

        return template, fingerprint
