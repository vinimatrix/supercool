import type { AnalysisReport } from "../../api/youtube";

interface YouTubeAIReportProps {
  report: AnalysisReport | null;
  onAnalyze: () => void;
  loading: boolean;
  provider: string;
  onProviderChange: (p: string) => void;
}

export function YouTubeAIReport({ report, onAnalyze, loading, provider, onProviderChange }: YouTubeAIReportProps) {
  return (
    <div style={{ padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ color: "#fff", margin: 0 }}>AI Analysis</h3>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <select
            value={provider}
            onChange={(e) => onProviderChange(e.target.value)}
            style={{ padding: "6px 12px", background: "#1a1a1a", color: "#fff", border: "1px solid #444", borderRadius: "4px" }}
          >
            <option value="groq">Groq (Cloud)</option>
            <option value="ollama">Ollama (Local)</option>
          </select>
          <button
            onClick={onAnalyze}
            disabled={loading}
            style={{ padding: "8px 16px", background: loading ? "#666" : "#8b5cf6", color: "#fff", border: "none", borderRadius: "4px", cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Analyzing..." : "Analyze with AI"}
          </button>
        </div>
      </div>

      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
            <h4 style={{ color: "#8b5cf6", marginBottom: "8px" }}>Summary</h4>
            <p style={{ color: "#fff", margin: 0 }}>{report.summary}</p>
          </div>

          {report.trends.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#8b5cf6", marginBottom: "8px" }}>Trends</h4>
              <ul style={{ color: "#fff", margin: 0, paddingLeft: "20px" }}>
                {report.trends.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}

          {report.recommendations.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#4ade80", marginBottom: "8px" }}>Recommendations</h4>
              <ul style={{ color: "#fff", margin: 0, paddingLeft: "20px" }}>
                {report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {report.growth_predictions && Object.keys(report.growth_predictions).length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#fbbf24", marginBottom: "8px" }}>Growth Predictions</h4>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
                {Object.entries(report.growth_predictions).map(([key, value]) => (
                  <div key={key}>
                    <div style={{ color: "#888", fontSize: "12px" }}>{key.replace("_", " ")}</div>
                    <div style={{ color: "#fff", fontSize: "14px" }}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.improvement_areas.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#f87171", marginBottom: "8px" }}>Areas for Improvement</h4>
              <ul style={{ color: "#fff", margin: 0, paddingLeft: "20px" }}>
                {report.improvement_areas.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}

          <div style={{ color: "#666", fontSize: "12px", textAlign: "right" }}>
            Generated: {new Date(report.generated_at).toLocaleString()} · Data: {report.data_freshness}
          </div>
        </div>
      )}
    </div>
  );
}
