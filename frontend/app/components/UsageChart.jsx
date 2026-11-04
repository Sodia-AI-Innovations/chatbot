export default function UsageChart({ daily }) {
    if (daily.length === 0) {
        return <div className="chart-card"><p className="chart-empty">No usage in the last 30 days yet.</p></div>;
    }
    const max = Math.max(1, ...daily.map((d) => d.tokens));
    return (
        <div className="chart-card">
            <div className="bars">
                {daily.map((d) => (
                    <div key={d.day} className="bar"
                         title={`${d.day}: ${Number(d.tokens).toLocaleString("en-IN")} tokens`}
                         style={{ height: `${Math.max(4, (d.tokens / max) * 100)}%` }} />
                ))}
            </div>
            <div className="bars-axis">
                <span>{daily[0].day}</span>
                <span>{daily[daily.length - 1].day}</span>
            </div>
        </div>
    );
}