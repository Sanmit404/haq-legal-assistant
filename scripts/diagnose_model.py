import tomllib, httpx, json
from pathlib import Path
s=tomllib.loads(Path('.streamlit/secrets.toml').read_text())
headers={'x-goog-api-key':s['GEMINI_API_KEY']}
with httpx.Client(timeout=30) as c:
 r=c.get('https://generativelanguage.googleapis.com/v1beta/models',headers=headers)
 data=r.json()
 print('Available models:',[m['name'] for m in data.get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[])])
 r=c.post('https://generativelanguage.googleapis.com/v1beta/models/'+s['MODEL_NAME']+':generateContent',headers=headers,json={'contents':[{'parts':[{'text':'Reply with OK.'}]}]})
 print('Generation status:',r.status_code)
 if r.is_error:
  error=r.json().get('error',{})
  print('Error code:',error.get('status'))
  print('Safe message:',str(error.get('message','')).replace(s['GEMINI_API_KEY'],'[REDACTED]')[:1500])
 else:print('Generation succeeded')
