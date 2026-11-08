"""Bounded extraction, portable exports, encrypted backups and calendar reminders."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import os
from pathlib import Path
from datetime import date, datetime, timezone
from xml.sax.saxutils import escape
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from fpdf import FPDF
from PIL import Image
from pypdf import PdfReader
from .domain import Case, Reminder, export_json, import_json

MAX_FILE = 10 * 1024 * 1024
MAX_VAULT = 60 * 1024 * 1024
FONT_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'fonts'

def extract_file(name, data):
    if len(data) > MAX_FILE: raise ValueError('Please use a file smaller than 10 MB.')
    suffix = Path(name).suffix.lower()
    try:
        if suffix in ('.txt', '.md', '.csv'):
            return data.decode('utf-8-sig')[:60000], None
        if suffix == '.pdf':
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted: raise ValueError('This PDF is password protected. Upload an unlocked copy.')
            if len(reader.pages) > 40: raise ValueError('Please split this PDF into sections of 40 pages or fewer.')
            text = '\n\n'.join(f'[Page {i+1}]\n{p.extract_text() or "[No readable text]"}' for i,p in enumerate(reader.pages))
            if len(text) > 60000: raise ValueError('This PDF contains too much text. Split it into smaller documents.')
            if sum(len(p.extract_text() or '') for p in reader.pages) < 80:
                return '', ('application/pdf', data)
            return text, None
        if suffix in ('.jpg', '.jpeg', '.png', '.webp'):
            img = Image.open(io.BytesIO(data))
            if img.width * img.height > 25_000_000: raise ValueError('Image is too large. Resize below 25 megapixels.')
            img.verify()
            img = Image.open(io.BytesIO(data)).convert('RGB')
            img.thumbnail((2400,2400))
            out = io.BytesIO(); img.save(out, format='JPEG', quality=85)
            return '', ('image/jpeg', out.getvalue())
        raise ValueError('Supported files: PDF, TXT, MD, CSV, PNG, JPG and WEBP.')
    except ValueError: raise
    except Exception: raise ValueError('This file could not be read. Try a valid PDF, image, or UTF-8 text file.') from None


def pdf_bytes(title, text):
    pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=20)
    latin = FONT_DIR / 'NotoSans-Regular.ttf'
    devanagari = FONT_DIR / 'NotoSansDevanagari-Regular.ttf'
    if not latin.exists(): raise ValueError('The bundled document font is missing.')
    pdf.add_font('Noto', fname=str(latin))
    if devanagari.exists():
        pdf.add_font('Deva', fname=str(devanagari))
        pdf.set_fallback_fonts(['Deva'])
    pdf.set_text_shaping(True)
    pdf.add_page(); pdf.set_font('Noto', size=10)
    pdf.set_text_color(19,117,102)
    pdf.cell(0,10,'HAQ / YOUR LEGAL ACTION WORKSPACE', new_x='LMARGIN',new_y='NEXT')
    pdf.set_text_color(24,45,41); pdf.set_font('Noto',size=19)
    pdf.multi_cell(0,10,title,new_x='LMARGIN',new_y='NEXT')
    pdf.ln(4); pdf.set_font('Noto',size=10)
    # Strip unsupported decorative emoji, preserve Indian scripts and currency.
    for line in text.splitlines():
        line = ''.join(c for c in line if ord(c) < 0x1F000)
        pdf.multi_cell(0,6,line or ' ',new_x='LMARGIN',new_y='NEXT',wrapmode='CHAR')
    pdf.ln(8); pdf.set_text_color(105,115,111); pdf.set_font('Noto',size=8)
    pdf.multi_cell(0,5,'Prepared with Haq. User review required. This document is not filed, served, notarised, or advocate-reviewed unless separately arranged.',new_x='LMARGIN',new_y='NEXT')
    return bytes(pdf.output())


def docx_bytes(title,text):
    doc=Document(); section=doc.sections[0]
    section.top_margin=Inches(.8); section.bottom_margin=Inches(.8)
    normal=doc.styles['Normal']; normal.font.name='Calibri'; normal.font.size=Pt(11)
    normal.font.color.rgb=RGBColor.from_string('182D29')
    doc.add_paragraph('HAQ / YOUR LEGAL ACTION WORKSPACE','Subtitle')
    doc.add_heading(title,0)
    for line in text.splitlines(): doc.add_paragraph(line)
    doc.add_paragraph('Prepared with Haq. Review before use. Not filed, served, notarised or advocate-reviewed.','Caption')
    out=io.BytesIO(); doc.save(out); return out.getvalue()


def handoff(case):
    lines=[case.title, f'Category: {case.category}', f'Location: {case.location or "Not confirmed"}',
           f'Desired outcome: {case.goal or "Not confirmed"}',f'Preference: {case.preference}',
           f'Existing proceedings: {case.prior_proceedings}',f'Status: {case.status}',
           '\nUSER ACCOUNT (unverified)',case.story,'\nFACTS']
    for f in case.facts:
        lines.append(f'- {f.label}: {f.value} [{f.status}; {"confirmed by user" if f.confirmed else "needs confirmation"}]')
        if f.quote: lines.append(f'  Evidence {f.source_id}: {f.quote}')
    lines.append('\nTIMELINE')
    lines.extend(f'- {e.date}: {e.description} [{e.source}]' for e in sorted(case.events,key=lambda e:e.date))
    lines.append('\nEVIDENCE INDEX')
    lines.extend(f'- {e.id}: {e.name} ({e.category})' for e in case.evidence)
    lines.append('\nQUESTIONS FOR PROFESSIONAL REVIEW')
    lines.extend(['- Does the proposed route apply to these facts and jurisdiction?', '- Are any urgent deadlines or overlapping proceedings relevant?', '- What additional evidence or documents are needed?'])
    return '\n'.join(lines)


def _key(password,salt):
    if len(password) < 12: raise ValueError('Use a passphrase of at least 12 characters.')
    return base64.urlsafe_b64encode(Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(password.encode()))


def encrypt_backup(case, originals, password):
    salt=os.urandom(16)
    obj={'case':case.model_dump(),'files':{k:base64.b64encode(v).decode() for k,v in originals.items() if any(e.id==k for e in case.evidence)}}
    data=json.dumps(obj,ensure_ascii=False).encode()
    if len(data)>MAX_VAULT: raise ValueError('Backup exceeds 60 MB. Reduce the number of originals before exporting.')
    return b'HAQ1'+salt+Fernet(_key(password,salt)).encrypt(data)


def decrypt_backup(data,password):
    if len(data)>MAX_VAULT*2 or not data.startswith(b'HAQ1'): raise ValueError('This is not a supported Haq encrypted backup.')
    try:
        payload=Fernet(_key(password,data[4:20])).decrypt(data[20:])
        obj=json.loads(payload); case=Case.model_validate(obj['case'])
        files={k:base64.b64decode(v,validate=True) for k,v in obj.get('files',{}).items() if any(e.id==k for e in case.evidence)}
        if sum(map(len,files.values()))>MAX_VAULT: raise ValueError('Backup files are too large.')
        return case,files
    except (InvalidToken, KeyError, TypeError, json.JSONDecodeError, ValueError):
        raise ValueError('Could not unlock this backup. Check the passphrase and file; your current case has not changed.') from None


def calendar_bytes(reminder):
    def esc(s): return s.replace('\\','\\\\').replace('\n','\\n').replace(';','\\;').replace(',','\\,').replace('\r','')
    d=date.fromisoformat(reminder.date).strftime('%Y%m%d')
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Haq//Case reminders//EN','BEGIN:VEVENT',
           f'UID:{reminder.id}@haq.local',f'DTSTAMP:{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}',
           f'DTSTART;VALUE=DATE:{d}','SUMMARY:Haq follow-up',
           'DESCRIPTION:Open your private Haq case to review your next action.',
           'BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:Haq follow-up','TRIGGER:-PT12H','END:VALARM','END:VEVENT','END:VCALENDAR']
    return ('\r\n'.join(lines)+'\r\n').encode()


def factual_template(case,kind='Initial complaint'):
    confirmed=[f for f in case.facts if f.confirmed and f.status not in ('Disputed','Unknown')]
    lines=[kind,'','To: [TO CONFIRM: recipient and verified address]',
           'Subject: '+case.title,'','Dear Sir / Madam,','',
           'I am writing regarding the following details from my account:']
    lines += [f'- {f.label}: {f.value}' for f in confirmed]
    if not confirmed:lines.append('[TO CONFIRM: transaction, dates, amount and relevant events]')
    lines += ['', 'Requested outcome: '+(case.goal or '[TO CONFIRM: requested outcome]'),
              '', 'Please review the information and provide a written response with the status and proposed next steps.',
              '', 'Attachments for review:']
    lines += [f'- {e.name}' for e in case.evidence] or ['[TO CONFIRM: relevant supporting documents]']
    lines += ['', 'Yours faithfully,','[TO CONFIRM: your name and contact details]',
              '', 'Preparation note: this factual template does not establish entitlement or set a legal deadline. Verify all details before use.']
    return '\n'.join(lines)
