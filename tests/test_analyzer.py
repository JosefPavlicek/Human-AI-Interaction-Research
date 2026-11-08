import unittest
from analyzer import normalize, windows, heuristic

class AnalyzerTests(unittest.TestCase):
    def test_plain_dialogue(self):
        turns,warning=normalize('User: Hello\nAI: Hi\nUser: Can you verify?')
        self.assertFalse(warning); self.assertEqual(len(turns),3)
        self.assertEqual(turns[1].role,'AI')
    def test_json(self):
        turns,_=normalize('[{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello"}]')
        self.assertEqual(len(turns),2)
    def test_multiline(self):
        turns,_=normalize('User: First\nsecond line\nAI: Reply')
        self.assertIn('second line',turns[0].text)
    def test_windows(self):
        turns,_=normalize('\n'.join(f'{"User" if i%2 else "AI"}: '+('word '*100) for i in range(15)))
        groups=windows(turns,max_chars=1100)
        self.assertGreater(len(groups),1)
        self.assertEqual(groups[-1][-1].number,len(turns))
    def test_no_false_claim(self):
        turns,_=normalize('User: Hello\nAI: Hi')
        self.assertEqual(heuristic(turns),[])

if __name__=='__main__': unittest.main()
