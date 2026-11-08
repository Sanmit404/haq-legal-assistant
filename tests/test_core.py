import io,json
from datetime import date
import pytest
from pypdf import PdfReader
from docx import Document
from haq.domain import Case,Fact,Reminder,SuggestedFact,supported_fact,urgency,redact
from haq.demo import demo_case
from haq.documents import encrypt_backup,decrypt_backup,extract_file,pdf_bytes,docx_bytes,calendar_bytes,handoff
from haq.provider import ModelClient,ModelConfig,ProviderError


def test_evidence_support_requires_exact_existing_quote():
 c=Case();e=c.add_evidence('receipt','Paid INR 3499 on 12 October')
 assert supported_fact(SuggestedFact(label='Amount',value='3499',source_id=e.id,quote='Paid INR 3499'),c).status=='Source-supported'
 assert supported_fact(SuggestedFact(label='Amount',value='9999',source_id=e.id,quote='Paid INR 9999'),c).status=='User-reported'
 assert supported_fact(SuggestedFact(label='Amount',value='3499',source_id='fake',quote='Paid INR 3499'),c).status=='User-reported'


def test_duplicate_evidence_and_revision():
 c=Case();c.add_evidence('a','test evidence');assert c.revision==2
 with pytest.raises(ValueError):c.add_evidence('b','test evidence')
 assert len(c.evidence)==1


def test_encrypted_backup_roundtrip_and_wrong_password():
 c=demo_case();files={c.evidence[0].id:b'original file'}
 encrypted=encrypt_backup(c,files,'correct horse battery staple')
 assert b'Headphones' not in encrypted
 restored,restored_files=decrypt_backup(encrypted,'correct horse battery staple')
 assert restored==c;assert restored_files==files
 with pytest.raises(ValueError):decrypt_backup(encrypted,'wrong horse battery staple')
 with pytest.raises(ValueError):decrypt_backup(encrypted[:-1]+b'X','correct horse battery staple')
 with pytest.raises(ValueError):encrypt_backup(c,{},'short')


def test_text_masking_and_urgency():
 output=redact('Aadhaar 1234 5678 9012 PAN ABCDE1234F email person@example.com mobile 9876543210')
 assert '1234 5678' not in output and 'ABCDE1234F' not in output and '@' not in output and '9876543210' not in output
 assert urgency('I was scammed through UPI')=='fraud'
 assert urgency('I am in immediate danger')=='danger'
 assert urgency('My refund is delayed') is None


def test_doc_exports_english_and_hindi():
 text='Amount: ₹3,499\nमुझे रिफंड चाहिए।\nPlease review the receipt.'
 pdf=pdf_bytes('Complaint draft',text)
 reader=PdfReader(io.BytesIO(pdf))
 assert len(reader.pages)>=1
 extracted=''.join(p.extract_text() for p in reader.pages)
 assert '3,499' in extracted and 'receipt' in extracted
 doc=Document(io.BytesIO(docx_bytes('Complaint draft',text)))
 assert any('मुझे रिफंड चाहिए' in p.text for p in doc.paragraphs)


def test_file_extraction_rejects_invalid_inputs():
 assert extract_file('a.txt',b'hello')[0]=='hello'
 with pytest.raises(ValueError):extract_file('a.pdf',b'bad pdf')
 with pytest.raises(ValueError):extract_file('a.exe',b'not allowed')
 with pytest.raises(ValueError):extract_file('a.txt',b'x'*(10*1024*1024+1))


def test_calendar_does_not_disclose_case_details():
 r=Reminder(title='Sensitive landlord dispute',date='2026-11-10',kind='Suggested follow-up')
 ics=calendar_bytes(r)
 assert b'Sensitive' not in ics and b'DTSTART;VALUE=DATE:20261110' in ics


def test_provider_filters_unknown_source_and_external_links(monkeypatch):
 client=ModelClient(ModelConfig(api_key='test'))
 data={'answer':'Read https://malicious.example', 'source_ids':['fake','nch']}
 monkeypatch.setattr(client,'_request',lambda *a,**k:{'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(data)}]}}]})
 answer=client.generate('test',{})
 assert answer.source_ids==['nch'] and 'https://' not in answer.answer


def test_provider_does_not_apply_truncated_or_malformed_answer(monkeypatch):
 client=ModelClient(ModelConfig(api_key='test'))
 for candidate in [{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'{}'}]}},{'finishReason':'STOP','content':{'parts':[{'text':'not json'}]}}]:
  monkeypatch.setattr(client,'_request',lambda *a,**k:{'candidates':[candidate]})
  with pytest.raises(ProviderError):client.generate('test',{})


def test_provider_missing_key_and_unsafe_endpoint():
 with pytest.raises(ProviderError):ModelClient(ModelConfig()).generate('test',{})
 with pytest.raises(ProviderError):ModelClient(ModelConfig(provider='compatible',api_key='test',base_url='http://localhost')).generate('test',{})


def test_handoff_marks_unconfirmed_facts():
 c=demo_case();text=handoff(c)
 assert 'needs confirmation' in text and 'Not sure' not in text and 'EVIDENCE INDEX' in text


def test_offline_template_excludes_unconfirmed_and_disputed_facts():
 from haq.documents import factual_template
 c=Case(goal='Refund')
 c.facts=[Fact(label='Payment',value='3499',confirmed=True),Fact(label='Unproven penalty',value='99999',confirmed=False),Fact(label='Disputed date',value='1 January',status='Disputed',confirmed=True)]
 text=factual_template(c)
 assert '3499' in text and '99999' not in text and '1 January' not in text


def test_working_draft_and_clarifications_survive_backup():
 c=Case(working_draft={'text':'edited draft','revision':1,'kind':'Complaint','id':'1'},messages=[{'role':'user','content':'The corrected amount is 3499'}])
 assert '3499' in c.context()['user_clarifications'][0]
 restored,_=decrypt_backup(encrypt_backup(c,{},'twelve characters pass'),'twelve characters pass')
 assert restored.working_draft['text']=='edited draft'
