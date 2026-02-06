"""
Insight detection from transcripts.
Uses regex patterns + optional LLM for summaries.
"""
import asyncio
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from src.transcription.transcriber import TranscriptChunk


class InsightType(Enum):
    REVENUE = "revenue"
    GROWTH = "growth"
    RISK = "risk"
    GUIDANCE = "guidance"
    TOPIC = "topic"


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class Insight:
    type: InsightType
    text: str
    sentiment: Sentiment = Sentiment.NEUTRAL
    confidence: float = 0.7
    timestamp: float = 0.0


@dataclass
class InsightResult:
    chunk: TranscriptChunk
    insights: List[Insight] = field(default_factory=list)
    rolling_summary: str = ""


# keyword patterns
PATTERNS = {
    InsightType.REVENUE: re.compile(r'revenue|sales|profit|earnings|income', re.I),
    InsightType.GROWTH: re.compile(r'\d+%|percent|growth|increase|grew', re.I),
    InsightType.RISK: re.compile(r'risk|decline|challenge|issue|problem|concern', re.I),
    InsightType.GUIDANCE: re.compile(r'expect|plan|goal|target|forecast|next', re.I),
    InsightType.TOPIC: re.compile(r'about|discuss|talk|mention|point|saying', re.I),
}

POSITIVE_WORDS = {'good', 'great', 'growth', 'increase', 'strong', 'positive', 'better', 'success'}
NEGATIVE_WORDS = {'bad', 'decline', 'risk', 'weak', 'concern', 'issue', 'problem', 'difficult'}


class InsightDetector:
    def __init__(self, use_llm=True):
        self.insights = []
        self.summary = ""
        self.text_buffer = []
        self.llm = None
        self.model = ""
        
        if use_llm:
            self._setup_llm()
    
    def _setup_llm(self):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            return
        
        groq_key = os.getenv("GROQ_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if groq_key:
            self.llm = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            self.model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        elif openrouter_key:
            self.llm = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)
            self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
        elif openai_key:
            self.llm = AsyncOpenAI(api_key=openai_key)
            self.model = "gpt-3.5-turbo"
    
    async def analyze(self, chunk: TranscriptChunk) -> InsightResult:
        found = self._find_insights(chunk.text)
        self.insights.extend(found)
        
        self.text_buffer.append(chunk.text)
        limit = 2 if not self.summary else 10
        
        if len(self.text_buffer) >= limit:
            self.summary = await self._get_summary()
            self.text_buffer = []
        
        return InsightResult(chunk=chunk, insights=found, rolling_summary=self.summary)
    
    def _find_insights(self, text):
        results = []
        words = set(text.lower().split())
        
        for itype, pattern in PATTERNS.items():
            match = pattern.search(text)
            if match:
                if words & POSITIVE_WORDS:
                    sent = Sentiment.POSITIVE
                elif words & NEGATIVE_WORDS:
                    sent = Sentiment.NEGATIVE
                else:
                    sent = Sentiment.NEUTRAL
                
                results.append(Insight(
                    type=itype,
                    text=match.group(),
                    sentiment=sent
                ))
        
        return results
    
    async def _get_summary(self):
        if not self.llm:
            return self.summary
        
        new_text = " ".join(self.text_buffer)
        prompt = f'Update this summary with new info. Keep it short (2-3 sentences).\n\nCurrent: "{self.summary}"\n\nNew text: "{new_text}"\n\nUpdated summary:'
        
        for i in range(3):
            try:
                resp = await self.llm.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep(2 ** (i + 1))
                else:
                    break
        
        return self.summary
    
    def get_final_summary(self):
        if not self.insights:
            return "No key points found."
        
        lines = ["Key Points:"]
        for ins in self.insights[:10]:
            lines.append(f"  - {ins.type.value}: {ins.text}")
        return "\n".join(lines)
