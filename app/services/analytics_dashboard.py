"""Analytics and monetization dashboard for SuperCool projects.

Tracks views, watch hours, CPM, and revenue across distribution channels.
Projects future earnings based on growth rates.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProjectMetrics:
    """Metrics for a single project."""
    project_id: str
    title: str
    views: int = 0
    watch_hours: float = 0.0
    cpm: float = 2.0
    revenue: float = 0.0
    platform: str = "youtube"
    published_at: datetime | None = None

    @property
    def estimated_revenue(self) -> float:
        """Calculate estimated revenue from views and CPM."""
        return (self.views / 1000) * self.cpm


@dataclass
class Dashboard:
    """Aggregated analytics dashboard."""
    projects: list[ProjectMetrics] = field(default_factory=list)

    def add_project(self, metrics: ProjectMetrics):
        self.projects.append(metrics)

    @property
    def total_views(self) -> int:
        return sum(p.views for p in self.projects)

    @property
    def total_watch_hours(self) -> float:
        return sum(p.watch_hours for p in self.projects)

    @property
    def total_revenue(self) -> float:
        return sum(p.estimated_revenue for p in self.projects)

    @property
    def average_cpm(self) -> float:
        if not self.projects:
            return 0.0
        return sum(p.cpm for p in self.projects) / len(self.projects)

    def project_earnings(self) -> list[dict]:
        """Get earnings breakdown per project."""
        return [
            {
                "title": p.title,
                "views": p.views,
                "revenue": round(p.estimated_revenue, 2),
                "platform": p.platform,
            }
            for p in sorted(self.projects, key=lambda x: x.estimated_revenue, reverse=True)
        ]

    def project_future_earnings(self, months: int = 6, monthly_growth_rate: float = 0.15) -> list[dict]:
        """Project future earnings for each month based on growth rate.

        Args:
            months: Number of months to project.
            monthly_growth_rate: Compound monthly growth rate (e.g., 0.15 = 15%).

        Returns:
            List of monthly projections.
        """
        projections = []
        current_views = self.total_views
        current_revenue = self.total_revenue

        for month in range(1, months + 1):
            current_views = int(current_views * (1 + monthly_growth_rate))
            current_revenue = current_revenue * (1 + monthly_growth_rate)
            projections.append({
                "month": month,
                "projected_views": current_views,
                "projected_revenue": round(current_revenue, 2),
            })

        return projections

    def summary(self) -> str:
        """Generate a formatted summary."""
        lines = [
            "=== SUPERCOOL ANALYTICS DASHBOARD ===",
            f"Total Projects: {len(self.projects)}",
            f"Total Views: {self.total_views:,}",
            f"Total Watch Hours: {self.total_watch_hours:,.1f}",
            f"Average CPM: ${self.average_cpm:.2f}",
            f"Total Revenue: ${self.total_revenue:,.2f}",
            "",
            "--- Project Breakdown ---",
        ]
        for p in self.project_earnings():
            lines.append(f"  {p['title']}: {p['views']:,} views = ${p['revenue']:.2f}")
        return "\n".join(lines)


if __name__ == "__main__":
    dashboard = Dashboard()

    # Example data
    dashboard.add_project(ProjectMetrics(
        project_id="1", title="Boruto: TBV - Scene 1",
        views=120000, watch_hours=4500, cpm=2.5, platform="youtube"
    ))
    dashboard.add_project(ProjectMetrics(
        project_id="2", title="Boruto: TBV - Full Episode",
        views=350000, watch_hours=12000, cpm=3.0, platform="youtube"
    ))

    print(dashboard.summary())
    print("\n--- 6-Month Projection (15% growth) ---")
    for proj in dashboard.project_future_earnings():
        print(f"  Month {proj['month']}: {proj['projected_views']:,} views = ${proj['projected_revenue']:,.2f}")
