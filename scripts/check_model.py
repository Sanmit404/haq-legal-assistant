from pathlib import Path
import sys,tomllib
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from haq.provider import ModelConfig,ModelClient,ProviderError
secret=tomllib.loads(Path('.streamlit/secrets.toml').read_text())
client=ModelClient(ModelConfig(api_key=secret.get('GEMINI_API_KEY',''),model=secret.get('MODEL_NAME','gemini-3.8-flash')))
try:
 models=client.models()
 print('Authentication succeeded. Available text models:',len(models))
 print('Configured model available:',client.config.model in models)
 result=client.generate('Ask one useful follow-up question for this synthetic refund case.',{'language':'English','story':'I returned headphones and have not received my refund.','goal':'Refund'})
 print('Structured response valid:',bool(result.answer))
 Path('output/test-results').mkdir(parents=True,exist_ok=True)
 Path('output/test-results/live-model-check.json').write_text(result.model_dump_json(indent=2))
except ProviderError as e:
 print('Model check failed:',str(e))
 sys.exit(1)
