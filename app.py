"""HAIR: exploratory human–AI dialogue analysis (standard library only)."""
import csv
import json
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

PATTERNS = {
    'explicit_acceptance': [r'\b(?:you are right|i agree|makes sense|souhlas[ií]m|m[aá]š pravdu|to d[aá]v[aá] smysl)\b'],
    'authority_deference': [r'\b(?:i trust you|if you say so|v[eě]ř[ií]m ti|kdy[zž] to [rř][ií]k[aá]š|spol[eé]h[aá]m na tebe)\b'],
    'position_shift': [r'\b(?:you convinced me|i changed my mind|p[rř]esv[eě]d[čc]il[ao]? (?:jsi )?m[eě]|zm[eě]nil[ao]? jsem n[aá]zor)\b'],
    'verification': [r'\b(?:source|evidence|citation|verify|prove|zdroj|d[uů]kaz|ov[eě][rř]|dolo[zž])\b'],
    'disagreement': [r'\b(?:i disagree|that is wrong|not true|nesouhlas[ií]m|to nen[ií] pravda|to je [šs]patn[eě])\b'],
}
REGEX = {k: [re.compile(p, re.I) for p in v] for k, v in PATTERNS.items()}
ROLE = re.compile(r'^\s*(?:\[)?(human|user|uživatel|uzivatel|člověk|clovek|assistant|ai|chatgpt|asistent)(?:\])?\s*:\s*(.*)$', re.I)

def parse(text):
    text = text.strip()
    if text.startswith('['):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                data = data.get('messages', [])
            if isinstance(data, list):
                out = []
                for m in data:
                    if not isinstance(m, dict): continue
                    role = str(m.get('role', m.get('speaker', ''))).lower()
                    content = m.get('content', m.get('text', ''))
                    if isinstance(content, list):
                        content = ' '.join(str(x.get('text', '')) if isinstance(x, dict) else str(x) for x in content)
                    if role in ('user', 'human', 'assistant', 'ai'):
                        out.append({'role': 'human' if role in ('user', 'human') else 'ai', 'text': str(content)})
                if out: return out
        except (ValueError, TypeError): pass
    out = []
    for line in text.splitlines():
        m = ROLE.match(line)
        if m:
            role = 'human' if m.group(1).lower() in ('human','user','uživatel','uzivatel','člověk','clovek') else 'ai'
            out.append({'role':role, 'text':m.group(2)})
        elif out:
            out[-1]['text'] += '\n' + line
    return out

def analyze(turns):
    results = []
    last_human_disagreed = False
    for i, t in enumerate(turns):
        if t['role'] != 'human': continue
        labels = [k for k, pats in REGEX.items() if any(p.search(t['text']) for p in pats)]
        prev_ai = next((turns[j]['text'] for j in range(i-1, -1, -1) if turns[j]['role']=='ai'), '')
        candidate = bool(prev_ai and ('authority_deference' in labels or 'position_shift' in labels or ('explicit_acceptance' in labels and last_human_disagreed)))
        if labels:
            results.append({'turn':i+1, 'labels':', '.join(labels), 'candidate':candidate, 'human_text':t['text'], 'preceding_ai_text':prev_ai})
        if 'disagreement' in labels: last_human_disagreed = True
        elif 'explicit_acceptance' in labels or 'position_shift' in labels: last_human_disagreed = False
    return results

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('HAIR — Exploratory Dialogue Analyzer v0.1')
        self.geometry('1050x690')
        self.results = []
        self.turns = []
        bar = ttk.Frame(self, padding=12); bar.pack(fill='x')
        ttk.Button(bar, text='Open TXT / JSON', command=self.load).pack(side='left')
        ttk.Button(bar, text='Export CSV', command=self.export).pack(side='left', padx=8)
        ttk.Button(bar, text='Load example', command=self.example).pack(side='left')
        self.status = ttk.Label(bar, text='No dialogue loaded'); self.status.pack(side='right')
        ttk.Label(self, text='Signals are heuristic candidates, NOT proof of persuasion or uncritical acceptance.', padding=(12,0)).pack(anchor='w')
        cols = ('turn','labels','candidate','human_text')
        self.table = ttk.Treeview(self, columns=cols, show='headings', height=14)
        for col, width in [('turn',60),('labels',230),('candidate',100),('human_text',620)]:
            self.table.heading(col, text=col.replace('_',' ').title()); self.table.column(col, width=width)
        self.table.pack(fill='both', expand=True, padx=12, pady=10)
        self.table.bind('<<TreeviewSelect>>', self.detail)
        ttk.Label(self, text='Selected event and preceding AI message', padding=(12,0)).pack(anchor='w')
        self.preview = tk.Text(self, height=12, wrap='word'); self.preview.pack(fill='both', expand=True, padx=12, pady=(4,12))
    def show(self):
        for item in self.table.get_children(): self.table.delete(item)
        self.results = analyze(self.turns)
        for n, r in enumerate(self.results):
            self.table.insert('', 'end', iid=str(n), values=(r['turn'],r['labels'],'YES' if r['candidate'] else 'no',r['human_text'].replace('\n',' ')[:180]))
        self.status.config(text=f'{len(self.turns)} turns | {len(self.results)} signals | {sum(r["candidate"] for r in self.results)} candidates')
        self.preview.delete('1.0','end')
    def load(self):
        path = filedialog.askopenfilename(filetypes=[('Dialogue', '*.txt *.json'),('All files','*.*')])
        if not path: return
        try:
            self.turns = parse(Path(path).read_text(encoding='utf-8-sig'))
            if not self.turns: raise ValueError('No recognized role-prefixed dialogue turns. Use User: / AI: lines or a JSON message array.')
            self.show()
        except Exception as e: messagebox.showerror('Load failed', str(e))
    def example(self):
        self.turns = parse('AI: This is definitely the best method.\nUser: I disagree; do you have evidence?\nAI: The results clearly prove it.\nUser: You convinced me, I agree.\nAI: Great.\nUser: Can you provide a source?')
        self.show()
    def detail(self, _event=None):
        sel = self.table.selection()
        if not sel: return
        r = self.results[int(sel[0])]
        self.preview.delete('1.0','end')
        self.preview.insert('end', f'AI (preceding):\n{r["preceding_ai_text"]}\n\nHUMAN (turn {r["turn"]}):\n{r["human_text"]}\n\nTags: {r["labels"]}\nCandidate: {r["candidate"]}\n')
    def export(self):
        if not self.results: messagebox.showinfo('Export','No signals to export'); return
        path = filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not path: return
        with open(path,'w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['turn','labels','candidate','human_text','preceding_ai_text']);writer.writeheader();writer.writerows(self.results)
        messagebox.showinfo('Export',f'Saved {len(self.results)} signals')
if __name__ == '__main__': App().mainloop()
