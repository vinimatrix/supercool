"""AI-powered YouTube analytics analysis using Groq/Ollama."""

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class AnalysisReport:
    summary: str = ""
    trends: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    growth_predictions: dict[str, Any] = field(default_factory=dict)
    top_performing: list[dict[str, Any]] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)
    charts_data: dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""
    data_freshness: str = "simulated"


class YouTubeAIAnalyst:
    """Generates AI-powered analysis reports from YouTube data."""

    def __init__(self, provider: str = "groq"):
        self.provider = provider
        self._http = httpx.AsyncClient(timeout=60)

    async def close(self):
        await self._http.aclose()

    async def analyze(self, youtube_data: dict[str, Any]) -> AnalysisReport:
        """Generate full analysis report from YouTube data."""
        prompt = self._build_prompt(youtube_data)

        if self.provider == "ollama":
            response = await self._call_ollama(prompt)
        else:
            response = await self._call_groq(prompt)

        return self._parse_report(response)

    def _build_prompt(self, data: dict[str, Any]) -> str:
        """Build structured prompt for LLM."""
        return f"""Eres un analista de YouTube experto. Analiza los siguientes datos y genera un reporte completo en español.

Datos del Canal:
- Suscriptores: {data.get('subscriber_count', 0):,}
- Views totales: {data.get('total_views', 0):,}
- Watch time: {data.get('watch_hours', 0):,.1f} horas
- Videos: {data.get('video_count', 0)}

Rendimiento de Videos:
{json.dumps(data.get('videos', []), indent=2, ensure_ascii=False)}

Demografía:
{json.dumps(data.get('demographics', {}), indent=2, ensure_ascii=False)}

Fuentes de Tráfico:
{json.dumps(data.get('traffic_sources', []), indent=2, ensure_ascii=False)}

Revenue:
{json.dumps(data.get('revenue', {}), indent=2, ensure_ascii=False)}

Retención:
{json.dumps(data.get('retention', []), indent=2, ensure_ascii=False)}

Genera un reporte JSON con esta estructura exacta:
{{
  "summary": "Resumen ejecutivo en 2-3 oraciones",
  "trends": ["tendencia 1", "tendencia 2", "tendencia 3"],
  "recommendations": ["recomendación 1", "recomendación 2", "recomendación 3"],
  "growth_predictions": {{
    "3_months": "predicción 3 meses",
    "6_months": "predicción 6 meses",
    "12_months": "predicción 12 meses"
  }},
  "top_performing": [{{"title": "video", "reason": "por qué es exitoso"}}],
  "improvement_areas": ["área 1", "área 2"]
}}

Responde SOLO con el JSON, sin texto adicional."""

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API for analysis."""
        api_key = os.environ.get("GROQ_API_KEY", "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")

        resp = await self._http.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for analysis."""
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")

        resp = await self._http.post(
            f"{ollama_url}/api/chat",
            json={
                "model": "llama3.1",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def _parse_report(self, response: str) -> AnalysisReport:
        """Parse LLM response into structured report."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            return AnalysisReport(
                summary=data.get("summary", ""),
                trends=data.get("trends", []),
                recommendations=data.get("recommendations", []),
                growth_predictions=data.get("growth_predictions", {}),
                top_performing=data.get("top_performing", []),
                improvement_areas=data.get("improvement_areas", []),
                generated_at=__import__("datetime").datetime.now().isoformat(),
                data_freshness="real",
            )
        except (json.JSONDecodeError, IndexError):
            # Fallback: treat entire response as summary
            return AnalysisReport(
                summary=response[:500],
                trends=[],
                recommendations=[],
                generated_at=__import__("datetime").datetime.now().isoformat(),
                data_freshness="real",
            )
