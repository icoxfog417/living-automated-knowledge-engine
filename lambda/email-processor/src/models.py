"""Data models for email processing."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailData:
    """Parsed email data."""
    sender: str
    subject: str
    body: str
    attachments: list[dict]
    message_id: str


@dataclass
class ProcessingResult:
    """Result of email processing."""
    success: bool
    message: str
    details: Optional[dict] = None
