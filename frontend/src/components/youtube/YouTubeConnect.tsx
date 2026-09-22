import { useState } from "react";

interface YouTubeConnectProps {
  onConnect: (token: string | null) => void;
  connected: boolean;
}

export function YouTubeConnect({ onConnect, connected }: YouTubeConnectProps) {
  const [token, setToken] = useState("");

  return (
    <div style={{ padding: "16px", borderBottom: "1px solid #333" }}>
      <h3 style={{ color: "#fff", marginBottom: "8px" }}>YouTube Studio</h3>
      {connected ? (
        <div style={{ color: "#4ade80" }}>
          ✓ Connected to YouTube Analytics
          <button
            onClick={() => onConnect(null)}
            style={{ marginLeft: "12px", padding: "4px 8px", background: "#ef4444", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
          >
            Disconnect
          </button>
        </div>
      ) : (
        <div>
          <input
            type="password"
            placeholder="YouTube Access Token (leave empty for demo)"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            style={{ width: "100%", padding: "8px", marginBottom: "8px", background: "#1a1a1a", color: "#fff", border: "1px solid #444", borderRadius: "4px" }}
          />
          <button
            onClick={() => onConnect(token || null)}
            style={{ width: "100%", padding: "8px", background: "#3b82f6", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
          >
            Connect YouTube
          </button>
        </div>
      )}
    </div>
  );
}
