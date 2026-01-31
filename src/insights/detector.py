"""
Real-Time Insight Detection Module

Extracts insights from transcript chunks using rule-based
patterns and optional LLM enhancement.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from src.transcription.transcriber import TranscriptChunk


class InsightType(Enum):
    """Types of financial insights to detect."""
    
    REVENUE = "revenue"
    GUIDANCE = "guidance"
    RISK = "risk"
    OUTLOOK = "outlook"
    GROWTH = "growth"
    MARGIN = "margin"
    MARKET_SHARE = "market_share"
    COMPETITION = "competition"
    REGULATION = "regulation"
    OTHER = "other"


class Sentiment(Enum):
    """Sentiment classification for insights."""
    
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class Insight:
    """Represents a detected insight."""
    
    type: InsightType
    text: str
    confidence: float = 1.0
    sentiment: Sentiment = Sentiment.NEUTRAL
    
    # Source information
    source_text: str = ""
    timestamp: float = 0.0


@dataclass
class InsightResult:
    """Result of insight detection for a transcript chunk."""
    
    # The transcript chunk that was analyzed
    chunk: TranscriptChunk
    
    # Detected insights
    insights: List[Insight] = field(default_factory=list)
    
    # Rolling summary (updated with each chunk)
    rolling_summary: str = ""
    
    # Key metrics mentioned
    metrics: dict = field(default_factory=dict)


# Patterns for detecting financial terms (Indian context)
FINANCIAL_PATTERNS = {
    InsightType.REVENUE: [
        r'revenue\s+(?:of|is|was|reached|grew|increased)?\s*(?:rs\.?|inr|₹)?\s*[\d,]+\s*(?:crore|lakh|million|billion)?',
        r'(?:rs\.?|inr|₹)\s*[\d,]+\s*(?:crore|lakh)\s+(?:revenue|turnover|sales)',
        r'top\s*line\s+(?:growth|of|at)',
        r'gross\s+revenue',
        r'net\s+sales',
    ],
    InsightType.GROWTH: [
        r'(?:grew|growth|increased|up)\s+(?:by\s+)?[\d.]+\s*%',
        r'[\d.]+\s*%\s+(?:growth|increase|rise)',
        r'yoy\s+(?:growth|increase)',
        r'year\s+on\s+year\s+(?:growth|increase)',
        r'qoq\s+(?:growth|increase)',
        r'quarter\s+on\s+quarter',
        r'cagr\s+of\s+[\d.]+\s*%',
    ],
    InsightType.MARGIN: [
        r'(?:ebitda|operating|gross|net|profit)\s+margin\s+(?:of|at|is|was)?\s*[\d.]+\s*%',
        r'[\d.]+\s*%\s+(?:ebitda|operating|gross|net)\s+margin',
        r'margin\s+(?:expansion|contraction|improvement|compression)',
        r'basis\s+points?\s+(?:improvement|expansion)',
    ],
    InsightType.GUIDANCE: [
        r'(?:guidance|outlook|expect|anticipate|project)',
        r'(?:next|coming)\s+(?:quarter|year|fiscal)',
        r'fy\s*\d{2,4}\s+(?:guidance|target)',
        r'we\s+(?:expect|anticipate|see|believe)',
        r'going\s+forward',
    ],
    InsightType.RISK: [
        r'(?:risk|challenge|headwind|concern|pressure)',
        r'(?:decline|decrease|drop|fell|down)\s+(?:by\s+)?[\d.]+\s*%',
        r'slowdown',
        r'uncertainty',
        r'volatility',
        r'stress',
    ],
    InsightType.OUTLOOK: [
        r'(?:positive|strong|robust|healthy)\s+(?:outlook|demand|momentum)',
        r'optimistic',
        r'confident\s+(?:about|in)',
        r'well\s+positioned',
        r'tailwind',
    ],
}

# Sentiment indicators
POSITIVE_WORDS = {
    'growth', 'increase', 'improvement', 'strong', 'robust', 'healthy',
    'positive', 'optimistic', 'confident', 'expansion', 'momentum',
    'outperform', 'exceed', 'record', 'highest', 'best'
}

NEGATIVE_WORDS = {
    'decline', 'decrease', 'drop', 'fell', 'pressure', 'challenge',
    'headwind', 'concern', 'risk', 'slowdown', 'weak', 'uncertainty',
    'volatile', 'stress', 'contraction', 'miss', 'below', 'lower'
}


class InsightDetector:
    """
    Real-time insight detection from transcript chunks.
    
    Uses rule-based pattern matching by default, with optional
    LLM enhancement when API keys are available.
    """
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize the insight detector.
        
        Args:
            use_llm: Whether to use LLM for insight extraction
        """
        self.use_llm = use_llm
        self.conversation_history: List[TranscriptChunk] = []
        self.all_insights: List[Insight] = []
        self.current_summary: str = ""
        
        # Check if LLM is available
        self.llm_client = None
        if use_llm:
            self._init_llm_client()
    
    def _init_llm_client(self):
        """Initialize LLM client if API key is available."""
        # Try OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=api_key)
                self.llm_provider = "openai"
                return
            except ImportError:
                pass
        
        # Try Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                import anthropic
                self.llm_client = anthropic.Anthropic(api_key=api_key)
                self.llm_provider = "anthropic"
                return
            except ImportError:
                pass
        
        # No LLM available
        self.llm_client = None
        self.use_llm = False
    
    async def analyze(self, chunk: TranscriptChunk) -> InsightResult:
        """
        Analyze a transcript chunk and extract insights.
        
        Args:
            chunk: The transcript chunk to analyze
            
        Returns:
            InsightResult with detected insights and updated summary
        """
        self.conversation_history.append(chunk)
        
        # Extract insights using rule-based approach
        insights = self._extract_insights_rule_based(chunk)
        
        # Optionally enhance with LLM
        if self.use_llm and self.llm_client:
            llm_insights = await self._extract_insights_llm(chunk)
            insights.extend(llm_insights)
        
        # Deduplicate insights
        insights = self._dedupe_insights(insights)
        
        # Store insights
        self.all_insights.extend(insights)
        
        # Update rolling summary
        rolling_summary = self._update_summary(chunk, insights)
        
        return InsightResult(
            chunk=chunk,
            insights=insights,
            rolling_summary=rolling_summary,
            metrics=self._extract_metrics(chunk.text)
        )
    
    def _extract_insights_rule_based(self, chunk: TranscriptChunk) -> List[Insight]:
        """Extract insights using pattern matching."""
        insights = []
        text_lower = chunk.text.lower()
        
        for insight_type, patterns in FINANCIAL_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    # Determine sentiment
                    sentiment = self._detect_sentiment(chunk.text)
                    
                    # Create insight
                    insight_text = self._summarize_match(insight_type, matches[0])
                    insights.append(Insight(
                        type=insight_type,
                        text=insight_text,
                        confidence=0.7,
                        sentiment=sentiment,
                        source_text=chunk.text[:100],
                        timestamp=chunk.start_time
                    ))
                    break  # One insight per type per chunk
        
        return insights
    
    def _detect_sentiment(self, text: str) -> Sentiment:
        """Detect sentiment from text."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        pos_count = len(words & POSITIVE_WORDS)
        neg_count = len(words & NEGATIVE_WORDS)
        
        if pos_count > neg_count + 1:
            return Sentiment.POSITIVE
        elif neg_count > pos_count + 1:
            return Sentiment.NEGATIVE
        return Sentiment.NEUTRAL
    
    def _summarize_match(self, insight_type: InsightType, match: str) -> str:
        """Create a human-readable summary of the match."""
        match = match.strip()
        
        summaries = {
            InsightType.REVENUE: f"Revenue mentioned: {match}",
            InsightType.GROWTH: f"Growth signal: {match}",
            InsightType.MARGIN: f"Margin data: {match}",
            InsightType.GUIDANCE: f"Forward guidance: {match}",
            InsightType.RISK: f"Risk factor: {match}",
            InsightType.OUTLOOK: f"Positive outlook: {match}",
        }
        
        return summaries.get(insight_type, match)
    
    def _extract_metrics(self, text: str) -> dict:
        """Extract numeric metrics from text."""
        metrics = {}
        
        # Find percentage values
        pct_matches = re.findall(r'([\d.]+)\s*%', text)
        if pct_matches:
            metrics['percentages'] = [float(p) for p in pct_matches]
        
        # Find rupee amounts
        rs_matches = re.findall(
            r'(?:rs\.?|inr|₹)\s*([\d,]+)\s*(crore|lakh|million)?',
            text, re.IGNORECASE
        )
        if rs_matches:
            metrics['amounts'] = rs_matches
        
        return metrics
    
    def _dedupe_insights(self, insights: List[Insight]) -> List[Insight]:
        """Remove duplicate insights."""
        seen = set()
        unique = []
        for insight in insights:
            key = (insight.type, insight.text[:50])
            if key not in seen:
                seen.add(key)
                unique.append(insight)
        return unique
    
    def _update_summary(self, chunk: TranscriptChunk, insights: List[Insight]) -> str:
        """Update the rolling summary with new information."""
        if not insights:
            return self.current_summary
        
        # Build summary from insights
        new_points = [i.text for i in insights[:3]]
        
        if self.current_summary:
            self.current_summary += " " + "; ".join(new_points)
        else:
            self.current_summary = "; ".join(new_points)
        
        # Keep summary manageable
        if len(self.current_summary) > 500:
            self.current_summary = self.current_summary[-500:]
        
        return self.current_summary
    
    async def _extract_insights_llm(self, chunk: TranscriptChunk) -> List[Insight]:
        """Extract insights using LLM (when available)."""
        if not self.llm_client:
            return []
        
        prompt = self._build_prompt(chunk)
        
        try:
            if self.llm_provider == "openai":
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                result = response.choices[0].message.content
            else:
                # Anthropic
                response = self.llm_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            
            return self._parse_llm_response(result, chunk)
        except Exception:
            return []
    
    def _build_prompt(self, chunk: TranscriptChunk) -> str:
        """Build prompt for LLM-based extraction."""
        return f"""Analyze this transcript from an Indian earnings call.
Extract key financial insights in JSON format.

Transcript: "{chunk.text}"

Return JSON with insights array, each having:
- type: revenue/growth/margin/guidance/risk/outlook
- text: brief description
- sentiment: positive/negative/neutral

Keep it brief. Only real insights."""
    
    def _parse_llm_response(
        self, 
        response: str, 
        chunk: TranscriptChunk
    ) -> List[Insight]:
        """Parse LLM response into Insight objects."""
        # Simple parsing - in production use proper JSON parsing
        insights = []
        try:
            import json
            data = json.loads(response)
            for item in data.get('insights', []):
                insight_type = InsightType(item.get('type', 'other'))
                sentiment = Sentiment(item.get('sentiment', 'neutral'))
                insights.append(Insight(
                    type=insight_type,
                    text=item.get('text', ''),
                    confidence=0.9,
                    sentiment=sentiment,
                    source_text=chunk.text[:100],
                    timestamp=chunk.start_time
                ))
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        return insights
    
    def get_final_summary(self) -> str:
        """Generate a final summary of the entire call."""
        if not self.all_insights:
            return "No significant insights detected during the call."
        
        # Group insights by type
        by_type = {}
        for insight in self.all_insights:
            type_name = insight.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(insight.text)
        
        # Build summary
        summary_parts = ["Call Summary:"]
        for type_name, texts in by_type.items():
            summary_parts.append(f"\n{type_name.upper()}:")
            for text in texts[:3]:  # Limit to top 3 per type
                summary_parts.append(f"  - {text}")
        
        return "\n".join(summary_parts)
    
    def get_key_insights(self) -> List[Insight]:
        """Get the most important insights detected so far."""
        return self.all_insights

