"""Match files against pattern rules.

This module uses Python's pathlib.PurePosixPath.match() for pattern matching,
which has the following characteristics:

1. **Partial Matching**: Patterns match against the end of the path
   - Pattern "*.txt" matches both "file.txt" and "docs/file.txt"
   - Pattern "README.md" matches both "README.md" and "docs/README.md"

2. **Deep Nesting Limitations**: Very deeply nested paths (4+ levels) may not
   match reliably with patterns like "reports/**/*.csv"

3. **No Brace Expansion**: Bash-style patterns like "*.{md,txt}" are not supported
   - Use separate rules for each extension instead

For more reliable matching, use explicit patterns with "**" prefix:
- Good: "**/*.txt" (explicit, matches all levels)
- Good: "reports/**/*.csv" (specific directory prefix)
- Caution: "*.txt" (matches any level, may be unexpected)
"""

from pathlib import PurePosixPath

from ..core.schema import MetadataRule


class RuleMatcher:
    """
    Match files against pattern rules using glob patterns.

    Important Limitations:
    - Uses pathlib.match() which matches against path suffixes
    - Very deep paths (4+ levels) may have unreliable matching
    - No support for brace expansion like {md,txt}

    See module docstring for detailed behavior information.
    """

    def __init__(self, rules: list[MetadataRule]):
        """
        Initialize rule matcher.

        Args:
            rules: List of metadata rules to match against
        """
        self.rules = rules

    def find_matching_rule(self, file_key: str) -> MetadataRule | None:
        """
        Find the first rule that matches the file key.

        Args:
            file_key: S3 object key to match

        Returns:
            Matching MetadataRule or None if no match found
        """
        for rule in self.rules:
            if self.match_pattern(file_key, rule.pattern):
                return rule

        return None

    @staticmethod
    def match_pattern(file_key: str, pattern: str) -> bool:
        """
        Match a file key against a glob pattern.

        This method handles both root-level and nested files correctly,
        including patterns with ** (globstar).

        Important Behavior Notes:
        - pathlib.match() matches against the END of the path
        - Pattern "*.txt" matches "file.txt" AND "docs/file.txt"
        - Pattern "README.md" matches "README.md" AND "docs/README.md"
        - For exact matching, use full path patterns

        Examples:
            >>> RuleMatcher.match_pattern("file.md", "**/*.md")
            True
            >>> RuleMatcher.match_pattern("docs/file.md", "**/*.md")
            True
            >>> RuleMatcher.match_pattern("reports/data.csv", "reports/**/*.csv")
            True
            >>> RuleMatcher.match_pattern("other/data.csv", "reports/**/*.csv")
            False

        Args:
            file_key: S3 object key to match (e.g., "docs/report.pdf")
            pattern: Glob pattern (e.g., "**/*.md", "reports/**/*.csv")

        Returns:
            True if the file key matches the pattern, False otherwise
        """
        # Use PurePosixPath for consistent path handling (S3 uses forward slashes)
        path = PurePosixPath(file_key)

        # Try direct match first
        if path.match(pattern):
            return True

        # For patterns starting with **, also try without the **/ prefix
        # This handles root-level files like "file.md" matching "**/*.md"
        if pattern.startswith("**/"):
            simple_pattern = pattern[3:]  # Remove "**/" prefix
            if path.match(simple_pattern):
                return True

        # For patterns with **/ in the middle (e.g., "reports/**/*.csv")
        # Try removing **/ entirely to match direct children
        if "/**/" in pattern:
            simple_pattern = pattern.replace("/**/", "/")
            if path.match(simple_pattern):
                return True

        return False
