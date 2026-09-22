import type { ChannelStats, VideoMetrics } from "../../api/youtube";

interface YouTubeDashboardProps {
  stats: ChannelStats | null;
  videos: VideoMetrics[];
}

export function YouTubeDashboard({ stats, videos }: YouTubeDashboardProps) {
  if (!stats) return null;

  const formatNumber = (n: number) => n.toLocaleString();
  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div style={{ padding: "16px" }}>
      <h3 style={{ color: "#fff", marginBottom: "12px" }}>Channel Overview</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "16px" }}>
        {[
          { label: "Subscribers", value: formatNumber(stats.subscriber_count) },
          { label: "Total Views", value: formatNumber(stats.total_view_count) },
          { label: "Watch Time", value: formatDuration(stats.total_watch_time_minutes * 60) },
          { label: "Videos", value: String(stats.video_count) },
        ].map((item) => (
          <div key={item.label} style={{ background: "#1a1a1a", padding: "12px", borderRadius: "8px", border: "1px solid #333" }}>
            <div style={{ color: "#888", fontSize: "12px" }}>{item.label}</div>
            <div style={{ color: "#fff", fontSize: "20px", fontWeight: "bold" }}>{item.value}</div>
          </div>
        ))}
      </div>

      <h3 style={{ color: "#fff", marginBottom: "12px" }}>Top Videos</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {videos.slice(0, 5).map((v) => (
          <div key={v.video_id} style={{ background: "#1a1a1a", padding: "12px", borderRadius: "8px", border: "1px solid #333", display: "flex", justifyContent: "space-between" }}>
            <div>
              <div style={{ color: "#fff", fontWeight: "bold" }}>{v.title}</div>
              <div style={{ color: "#888", fontSize: "12px" }}>
                {formatNumber(v.view_count)} views · {formatDuration(v.average_view_duration_seconds)} avg · {v.click_through_rate.toFixed(1)}% CTR
              </div>
            </div>
            <div style={{ color: "#4ade80", fontSize: "12px" }}>
              {v.average_view_percentage.toFixed(0)}% watched
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
