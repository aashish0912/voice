import os, asyncio
from dataclasses import dataclass, field

@dataclass
class InsightResult:
    chunk: object; insights: list = field(default_factory=list); rolling_summary: str = ""

class InsightDetector:
    def __init__(self):
        self.insights, self.summary, self.full_text, self.batch = [], "", [], []
        self.llm = self._setup_llm()
        
    def _setup_llm(self):
        try: from openai import AsyncOpenAI
        except: return None
        
        keys = [("GROQ", "https://api.groq.com/openai/v1"), ("OPENROUTER", "https://openrouter.ai/api/v1"), ("OPENAI", None)]
        for k, url in keys:
            if os.getenv(f"{k}_API_KEY"):
                return AsyncOpenAI(base_url=url, api_key=os.getenv(f"{k}_API_KEY"))
        return None

    async def analyze(self, chunk):
        self.full_text.append(chunk.text); self.batch.append(chunk.text)
        insights, summary = [], self.summary
        
        if len(self.batch) >= (2 if not self.summary else 10):
            insights = await self._call_llm(f"Extract insights (REVENUE, GROWTH, RISK, GUIDANCE, KEY_POINT) from: {' '.join(self.batch)}\nOnly output found info. Format: TYPE: text", 3)
            summary = await self._call_llm(f"Summarize this in 2-3 sentences:\n{' '.join(self.full_text)[-4000:]}", 1, is_summary=True)
            
            parsed = self._parse(insights)
            self.insights.extend(parsed)
            self.summary = summary if summary else self.summary
            self.batch = []
            
        return InsightResult(chunk, self._parse(insights, 3), self.summary)

    async def get_final_summary(self, text):
        if not self.llm or not text: return {"summary": "No summary", "insights": []}
        
        summary = await self._call_llm(f"Detailed 3-5 paragraph summary of:\n{text[:15000]}", 1, is_summary=True)
        insights = await self._call_llm(f"List key insights (KEY_POINT, RISK, GROWTH, REVENUE) for:\n{text[:10000]}\nOnly output if mentioned.\nFormat: TYPE: text", 15)
        
        final_insights = self._parse(insights)
        if not final_insights and self.insights: final_insights = self.insights
        
        return {"summary": summary, "insights": final_insights}

    def _parse(self, lines, limit=None):
        res = []
        skip_phrases = ["none", "no specific", "not mentioned", "n/a", "no information", "no revenue", "no growth", "no risk"]
        for l in lines:
            if ":" not in l: continue
            t, txt = l.split(":", 1)
            t = t.strip("* -").upper()
            txt_clean = txt.strip()
            
            if t in ["REVENUE", "GROWTH", "RISK", "GUIDANCE", "KEY_POINT"] and txt_clean:
                if not any(p in txt_clean.lower() for p in skip_phrases):
                    res.append({"type": t, "text": txt_clean})
        return res[:limit] if limit else res

    async def _call_llm(self, prompt, lines=1, is_summary=False):
        if not self.llm: return "" if is_summary else []
        
        # Default model logic
        model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        if "api.groq.com" not in str(self.llm.base_url):
            model = "gpt-3.5-turbo"
            
        try:
            resp = await self.llm.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}], max_tokens=600)
            text = resp.choices[0].message.content.strip()
            return text if is_summary else [l.strip() for l in text.split("\n")]
        except: return "" if is_summary else []
 
