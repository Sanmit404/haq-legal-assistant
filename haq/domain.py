from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


def uid(): return uuid4().hex[:12]
def now(): return datetime.now(timezone.utc).isoformat()

class Fact(BaseModel):
    id: str = Field(default_factory=uid)
    label: str = Field(max_length=200)
    value: str = Field(max_length=4000)
    status: Literal['User-reported', 'Source-supported', 'Disputed', 'Unknown'] = 'User-reported'
    source_id: str = ''
    quote: str = ''
    confirmed: bool = False

class Evidence(BaseModel):
    id: str = Field(default_factory=uid)
    name: str = Field(max_length=200)
    text: str = Field(max_length=60000)
    digest: str = ''
    category: str = 'Other'
    added: str = Field(default_factory=now)

class Draft(BaseModel):
    id: str = Field(default_factory=uid)
    kind: str
    text: str
    revision: int
    created: str = Field(default_factory=now)

class Event(BaseModel):
    id: str = Field(default_factory=uid)
    date: str
    description: str
    source: str = 'User-reported'

class Reminder(BaseModel):
    id: str = Field(default_factory=uid)
    title: str
    date: str
    kind: Literal['Suggested follow-up', 'Date in document', 'Professional-confirmed deadline']
    basis: str = ''
    done: bool = False

class Case(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    id: str = Field(default_factory=uid)
    title: str = 'My new case'
    category: Literal['Consumer purchase', 'Banking / payment', 'Rental / employment / other'] = 'Consumer purchase'
    language: Literal['English', 'Hindi', 'Hinglish'] = 'English'
    location: str = ''
    goal: str = ''
    preference: str = 'Try a free route first'
    story: str = ''
    facts: list[Fact] = Field(default_factory=list, max_length=100)
    evidence: list[Evidence] = Field(default_factory=list, max_length=30)
    events: list[Event] = Field(default_factory=list, max_length=100)
    reminders: list[Reminder] = Field(default_factory=list, max_length=100)
    drafts: list[Draft] = Field(default_factory=list, max_length=50)
    working_draft: dict = Field(default_factory=dict)
    messages: list[dict] = Field(default_factory=list, max_length=100)
    updates: list[dict] = Field(default_factory=list, max_length=100)
    analyses: list[dict] = Field(default_factory=list, max_length=100)
    revision: int = 1
    status: str = 'Building my case'
    reference: str = ''
    reference_basis: str = 'User-reported'
    prior_proceedings: str = 'Not sure'
    created: str = Field(default_factory=now)
    audit: list[dict] = Field(default_factory=list, max_length=500)

    def touch(self, action: str):
        self.revision += 1
        self.audit = (self.audit + [{'at': now(), 'action': action, 'revision': self.revision}])[-500:]

    def add_evidence(self, name, text, category='Other', digest=''):
        digest = digest or hashlib.sha256(text.encode()).hexdigest()
        if any(e.digest == digest for e in self.evidence):
            raise ValueError('This evidence is already in your case.')
        if len(self.evidence) >= 30: raise ValueError('A case can hold up to 30 evidence items.')
        e = Evidence(name=name, text=text, category=category, digest=digest)
        self.evidence.append(e)
        self.touch('Evidence added')
        return e

    def context(self):
        return {
            'category': self.category, 'language': self.language, 'location': self.location,
            'goal': self.goal, 'preference': self.preference, 'story': self.story,
            'facts': [f.model_dump() for f in self.facts],
            'evidence': [e.model_dump(exclude={'digest'}) for e in self.evidence],
            'timeline': [e.model_dump() for e in self.events],
            'prior_proceedings': self.prior_proceedings,
            'user_clarifications': [m['content'] for m in self.messages if m.get('role') == 'user'][-12:],
        }

class SuggestedFact(BaseModel):
    label: str
    value: str
    source_id: str = ''
    quote: str = ''

class Analysis(BaseModel):
    answer: str
    questions: list[str] = Field(default_factory=list, max_length=5)
    facts: list[SuggestedFact] = Field(default_factory=list, max_length=30)
    contradictions: list[str] = Field(default_factory=list, max_length=15)
    missing_evidence: list[str] = Field(default_factory=list, max_length=15)
    source_ids: list[str] = Field(default_factory=list, max_length=10)
    professional_review: bool = False
    review_reason: str = ''


def supported_fact(suggestion, case):
    source = next((e for e in case.evidence if e.id == suggestion.source_id), None)
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip().casefold()
    supported = bool(source and len(suggestion.quote.strip()) >= 8 and normalize(suggestion.quote) in normalize(source.text))
    return Fact(label=suggestion.label, value=suggestion.value,
                status='Source-supported' if supported else 'User-reported',
                source_id=source.id if supported else '', quote=suggestion.quote if supported else '')


def urgency(text):
    text = text.casefold()
    fraud = ['unauthorised transaction', 'unauthorized transaction', 'otp scam', 'financial fraud',
             'stole my money', 'upi scam', 'cyber fraud', 'पैसे चोरी', 'धोखाधड़ी', 'scammed']
    danger = ['immediate danger', 'threatened to kill', 'physical violence', 'suicide', 'kill myself', 'जान से मार']
    return 'danger' if any(t in text for t in danger) else 'fraud' if any(t in text for t in fraud) else None


def redact(text):
    text = re.sub(r'(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)', '[ID REDACTED]', text)
    text = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', '[PAN REDACTED]', text)
    text = re.sub(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)', '[LONG NUMBER REDACTED]', text)
    text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[EMAIL REDACTED]', text)
    text = re.sub(r'(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)', '[PHONE REDACTED]', text)
    return text


def export_json(case): return case.model_dump_json(indent=2).encode('utf-8')
def import_json(data):
    if len(data) > 8_000_000: raise ValueError('Backup is too large.')
    return Case.model_validate_json(data)
