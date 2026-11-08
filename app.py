"""HAIR alpha — browser UI for exploratory human–AI dialogue research."""
import csv
import io
import json
import os
import urllib.request
import streamlit as st
from analyzer import normalize, heuristic, analyze_ai, windows

# Stable application identifier for outgoing urllib requests.
# Groq/Cloudflare may reject urllib's default Python-urllib user agent.
# Keep this identifier independent of the application release number.
_http_opener = urllib.request.build_opener()
_http_opener.addheaders = [("User-Agent", "HAIR-Research")]
urllib.request.install_opener(_http_opener)

st.set_page_config(page_title='HAIR Alpha',layout='wide')
st.title('HAIR · Human–AI Interaction Research')
st.caption('Alpha research prototype · Candidate discourse mechanisms, not psychological diagnoses or causal proof.')
with st.sidebar:
    st.header('Analysis settings')
    use_ai=st.checkbox('Enable Groq AI analysis',value=True)
    if use_ai:
        key=st.text_input('Groq API key',type='password',value=os.environ.get('GROQ_API_KEY',''),help='Prefer a Codespaces secret named GROQ_API_KEY. Never commit a key.')
        model=st.text_input('Model ID',value='openai/gpt-oss-20b')
        st.warning('Groq receives the dialogue when you click Run AI analysis. Upload only data you have permission to share. Remove identifying details.')
    st.info('The rule-based baseline uses no external AI API. Codespaces itself is hosted remotely.')

uploaded=st.file_uploader('Upload dialogue (TXT or JSON)',type=['txt','json'])
if uploaded is not None:
    data=uploaded.getvalue().decode('utf-8-sig',errors='replace')
    if (st.session_state.get('uploaded_name'),st.session_state.get('uploaded_text'))!=(uploaded.name,data):
        st.session_state['dialogue']=data
        st.session_state['uploaded_name']=uploaded.name
        st.session_state['uploaded_text']=data
        st.session_state.pop('ai_result',None)
raw=st.text_area('Or paste dialogue (Ctrl+V)',key='dialogue',height=260,placeholder='User: I disagree. Can you show evidence?\nAI: Here is my reasoning...')
turns,warning=normalize(raw)
if warning and raw.strip(): st.warning(warning)
if turns:
    normalized='\n\n'.join(f'{t.role}: {t.text}' for t in turns)
    st.success(f'Recognized {len(turns)} turns ({sum(t.role=="User" for t in turns)} user, {sum(t.role=="AI" for t in turns)} AI).')
    st.download_button('Download normalized dialogue',normalized,file_name='hair_normalized.txt')
    with st.expander('Preview normalized turns'):
        for t in turns:
            st.markdown(f'**Turn {t.number} · {t.role}**')
            st.text(t.text)
    baseline=heuristic(turns)
    st.subheader(f'Rule-based baseline · {len(baseline)} candidates')
    if baseline: st.dataframe(baseline,hide_index=True,use_container_width=True)
    else: st.info('No lexical cues detected. This does not mean there are no meaningful discourse mechanisms.')
    st.download_button('Export baseline JSON',json.dumps(baseline,ensure_ascii=False,indent=2),file_name='hair_baseline.json',mime='application/json')
    st.divider()
    st.subheader('Contextual AI-assisted annotation')
    st.write('The model examines multi-turn context, highlights critical thinking and possible uncritical adoption, and provides alternative explanations. Evidence quotes are checked against the source text.')
    try:
        chunks=windows(turns)
        st.caption(f'{len(chunks)} analysis window(s), with overlap for context. Longer dialogues require multiple API requests.')
        can_run=True
    except ValueError as exc:
        st.error(str(exc)); can_run=False
    st.caption('If Groq runs out of JSON output tokens, HAIR automatically retries smaller dialogue windows. This can require extra API requests.')
    st.caption('Free-tier rate limits: if Groq returns HTTP 429, HAIR waits automatically and retries. Long or daily-limit delays may require trying again later.')
    if st.button('Run AI analysis',type='primary',disabled=not (use_ai and can_run)):
        if not key.strip(): st.error('Enter your Groq API key in the sidebar first.')
        else:
            try:
                progress=st.progress(0, text='Starting AI analysis…')
                notice=st.empty()
                def update_progress(done,total,waiting):
                    progress.progress(done / total, text=f'Analyzed {done} of {total} dialogue windows')
                    if waiting:
                        seconds,attempt,maximum=waiting
                        notice.info(f'Groq free-tier limit reached. Automatically waiting {seconds:.1f} seconds before retry {attempt}/{maximum}. No payment is needed.')
                    else:
                        notice.empty()
                result=analyze_ai(turns,key.strip(),model.strip(),on_progress=update_progress)
                progress.progress(1.0,text='Analysis completed')
                notice.empty()
                st.session_state['ai_result']=result
                st.session_state['ai_input']=normalized
                st.session_state['ai_model']=model.strip()
            except (RuntimeError,ValueError,TimeoutError) as exc:
                st.error(str(exc))
    result=st.session_state.get('ai_result')
    if use_ai and result and st.session_state.get('ai_input') == normalized and st.session_state.get('ai_model') == model.strip():
        st.subheader(f'AI candidate annotations · {len(result["events"])} events')
        if result['rejected_unverifiable_events']:
            st.warning(f'{result["rejected_unverifiable_events"]} model annotations were discarded because their quotes or turn references could not be verified.')
        for item in result['window_summaries']:
            st.markdown(f'**Turns {item["turns"]} · user stance: {item["user_stance"]}**')
            st.write(item['summary'])
        if result['events']:
            st.dataframe(result['events'],hide_index=True,use_container_width=True)
            st.markdown('**Human review** — annotate each candidate; the AI result alone is not a finding.')
            review=[]
            for i,e in enumerate(result['events']):
                with st.expander(f'Turn {e["turn"]}: {e["mechanism"]} — {e["evidence"][:95]}'):
                    st.write('**Evidence:**',e['evidence'])
                    st.write('**Interpretation:**',e['explanation'])
                    st.write('**Alternative explanation:**',e['alternative_explanation'])
                    decision=st.selectbox('Human decision',('not reviewed','supported','rejected','uncertain'),key=f'review_{i}_{e["turn"]}_{e["mechanism"]}')
                    note=st.text_area('Researcher note',key=f'note_{i}_{e["turn"]}_{e["mechanism"]}')
                    review.append({**e,'human_decision':decision,'human_note':note})
            out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=list(review[0])); writer.writeheader();writer.writerows(review)
            st.download_button('Export reviewed annotations CSV',out.getvalue(),file_name='hair_reviewed_annotations.csv',mime='text/csv')
        else: st.info('No verifiable AI events returned for these windows.')
        st.download_button('Export AI result JSON',json.dumps(result,ensure_ascii=False,indent=2),file_name='hair_ai_result.json',mime='application/json')
st.divider()
st.caption('Research limitations: LLM annotations can be biased or inconsistent. The app does not verify factual truth, infer private mental states, or establish causal persuasion. Validate with independent human raters.')
