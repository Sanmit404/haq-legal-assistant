from pathlib import Path
from streamlit.testing.v1 import AppTest
from haq.demo import demo_case
from haq.domain import Draft

ROOT=Path(__file__).resolve().parent.parent

def app(page='Overview',sample=False):
 at=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=30)
 at.secrets['GEMINI_API_KEY']=''
 if sample:
  c=demo_case();c.drafts=[Draft(kind='Initial complaint',text='Please review my refund of ₹3,499.',revision=c.revision)]
  at.session_state['cases']={c.id:c};at.session_state['active_id']=c.id
 at.session_state['page']=page
 return at.run()

def test_initial_page_and_all_workspace_pages_render():
 for page in ['Overview','My case','Evidence','My options','Documents','Updates & help','Settings']:
  at=app(page,sample=page!='Overview')
  assert not at.exception, f'{page}: {[x.value for x in at.exception]}'

def test_create_case_and_confirm_fact():
 at=app()
 next(x for x in at.text_input if x.label=='Give this case a name').set_value('Refund test')
 next(x for x in at.text_area if x.label=='Tell us what happened').set_value('I returned an item and need a refund.')
 next(x for x in at.button if x.label=='Create my case →').click().run()
 assert not at.exception
 assert at.session_state['page']=='My case'
 next(x for x in at.text_input if x.label=='New fact label').set_value('Amount')
 next(x for x in at.text_input if x.label=='New fact value').set_value('3499')
 next(x for x in at.checkbox if x.label=='I confirm this fact').check()
 next(x for x in at.button if x.label=='Add fact').click().run()
 c=at.session_state['cases'][at.session_state['active_id']]
 assert c.facts[0].confirmed and c.facts[0].value=='3499'
 assert not at.exception

def test_no_ai_without_consent():
 at=app('My case',True)
 next(x for x in at.button if x.label=='Help me understand my next step').click().run()
 assert any('Enable AI processing' in x.value for x in at.warning)
 assert not at.exception

def test_resolution_requires_fulfilment():
 at=app('Updates & help',True)
 next(x for x in at.selectbox if x.label=='Case progress').set_value('Resolved')
 next(x for x in at.button if x.label=='Update progress').click().run()
 c=at.session_state['cases'][at.session_state['active_id']]
 assert c.status!='Resolved'
 assert any('Confirm fulfilment' in x.value for x in at.warning)


def test_manual_handoff_document_works_without_model():
 at=app('Documents',True)
 next(x for x in at.selectbox if x.label=='What do you need?').set_value('Professional handoff')
 next(x for x in at.button if x.label=='Prepare draft').click().run()
 assert not at.exception
 assert any('EVIDENCE INDEX' in x.value for x in at.text_area)


def test_model_configuration_survives_navigation():
 at=app('Settings',True)
 next(x for x in at.text_input if x.label=='Model ID').set_value('test-model-for-persistence')
 next(x for x in at.button if x.label=='Apply model settings').click().run()
 next(x for x in at.button if x.label=='Overview').click().run()
 next(x for x in at.button if x.label=='Settings').click().run()
 assert next(x for x in at.text_input if x.label=='Model ID').value=='test-model-for-persistence'
 assert not at.exception


def test_working_document_survives_navigation():
 at=app('Documents',True)
 next(x for x in at.button if x.label=='Use a factual template · no AI needed').click().run()
 next(x for x in at.text_area if x.label=='Review and edit your draft').set_value('My edited factual complaint.').run()
 next(x for x in at.button if x.label=='My case').click().run()
 next(x for x in at.button if x.label=='Documents').click().run()
 assert next(x for x in at.text_area if x.label=='Review and edit your draft').value=='My edited factual complaint.'
 assert not at.exception
