"""Match files against pattern rules."""

import re

from ..core.schema import PathRule


class RuleMatcher:
    """Match files against pattern rules using glob patterns."""

    def __init__(self, rules: list[PathRule]):
        self.rules = rules

    def find_matching_rule(self, file_key: str) -> PathRule | None:
        """Find the first rule that matches the file key."""
        for rule in self.rules:
            if self.match_pattern(file_key, rule.pattern):
                return rule
        return None

    def extract_values(self, file_key: str, rule: PathRule) -> dict[str, str]:
        """Extract values from file path using rule pattern."""
        # Convert pattern to regex for value extraction
        regex_pattern = rule.pattern.replace('**', '.*').replace('*', '[^/]*')
        regex_pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', regex_pattern)
        
        match = re.match(f'^{regex_pattern}$', file_key)
        extracted = match.groupdict() if match else {}
        
        # Apply rule extractions (fixed values override path values)
        result = {}
        for field, template in rule.extractions.items():
            if template.startswith("{") and template.endswith("}"):
                var_name = template[1:-1]
                result[field] = extracted.get(var_name, "")
            else:
                result[field] = template
        return result

    @staticmethod
    def match_pattern(file_key: str, pattern: str) -> bool:
        """Check if file matches glob pattern, treating {var} as wildcards."""
        # Replace {variable} with * for glob matching
        glob_pattern = re.sub(r'\{[^}]+\}', '*', pattern)
        
        # Convert glob pattern to regex - handle ** before * to avoid conflicts
        regex_pattern = glob_pattern.replace('**', 'DOUBLESTAR_PLACEHOLDER')
        regex_pattern = regex_pattern.replace('*', '[^/]*')
        regex_pattern = regex_pattern.replace('DOUBLESTAR_PLACEHOLDER', '.*')
        
        return bool(re.match(f'^{regex_pattern}$', file_key))
