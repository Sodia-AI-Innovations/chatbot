export default function Stat({ icon: Icon, label, value, sub, highlight }) {
    return (
        <div className={`stat${highlight ? " highlight" : ""}`}>
            <span className="stat-icon"><Icon size={20} /></span>
            <div>
                <p className="stat-label">{label}</p>
                <p className="stat-value">{value}</p>
                {sub && <p className="stat-sub">{sub}</p>}
            </div>
        </div>
    );
}