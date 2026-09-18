import { api } from "./client";

export interface ChannelStats {
  subscriber_count: number;
  total_view_count: number;
  total_watch_time_minutes: number;
  video_count: number;
  channel_name: string;
  thumbnail_url: string;
}

export interface VideoMetrics {
  video_id: string;
  title: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  average_view_duration_seconds: number;
  average_view_percentage: number;
  click_through_rate: number;
  published_at: string;
}

export interface Demographics {
  age_groups: Record<string, number>;
  gender: Record<string, number>;
  geography: { country: string; views: number }[];
}

export interface TrafficSource {
  source: string;
  views: number;
  percentage: number;
}

export interface RevenueData {
  estimated_revenue: number;
  estimated_cpm: number;
  estimated_rpm: number;
  monthly_revenue: { month: string; revenue: number }[];
}

export interface RetentionPoint {
  second: number;
  retention_percentage: number;
}

export interface AnalysisReport {
  summary: string;
  trends: string[];
  recommendations: string[];
  growth_predictions: Record<string, string>;
  top_performing: { title: string; reason: string }[];
  improvement_areas: string[];
  charts_data: Record<string, unknown>;
  generated_at: string;
  data_freshness: string;
}

export const youtubeApi = {
  async getChannelStats(token: string | null): Promise<ChannelStats> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await api.get(`/youtube/analytics/channel${params}`);
    return resp.data;
  },

  async getVideoMetrics(token: string | null, videoIds?: string[]): Promise<VideoMetrics[]> {
    const params = new URLSearchParams();
    if (token) params.set("access_token", token);
    if (videoIds) params.set("video_ids", videoIds.join(","));
    const resp = await api.get(`/youtube/analytics/videos?${params}`);
    return resp.data;
  },

  async getDemographics(token: string | null): Promise<Demographics> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await api.get(`/youtube/analytics/demographics${params}`);
    return resp.data;
  },

  async getTrafficSources(token: string | null): Promise<TrafficSource[]> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await api.get(`/youtube/analytics/traffic${params}`);
    return resp.data;
  },

  async getRevenue(token: string | null): Promise<RevenueData> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await api.get(`/youtube/analytics/revenue${params}`);
    return resp.data;
  },

  async getRetention(token: string | null, videoId: string): Promise<RetentionPoint[]> {
    const params = new URLSearchParams();
    if (token) params.set("access_token", token);
    params.set("video_id", videoId);
    const resp = await api.get(`/youtube/analytics/retention?${params}`);
    return resp.data;
  },

  async getRealtimeViews(token: string | null, hours?: number): Promise<{ timestamp: string; views: number }[]> {
    const params = new URLSearchParams();
    if (token) params.set("access_token", token);
    if (hours) params.set("hours", String(hours));
    const resp = await api.get(`/youtube/analytics/realtime?${params}`);
    return resp.data;
  },

  async analyze(token: string | null, provider: string = "groq", videoIds?: string[]): Promise<AnalysisReport> {
    const resp = await api.post("/youtube/analyze", {
      access_token: token,
      ai_provider: provider,
      video_ids: videoIds,
    });
    return resp.data;
  },
};
