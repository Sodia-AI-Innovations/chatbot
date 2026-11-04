import { useState } from "react";
import { Link, useLoaderData } from "@remix-run/react";
import { Bot, ChevronRight, Search, Users, Wallet, Zap } from "lucide-react";
import { callApi } from "../api.server";
import Shell from "../components/Shell";
import Stat from "../components/Stat";
import UsageChart from "../components/UsageChart";

export const meta = () => [{ title: "Admin - Users" }];

export async function loader() {
    const [overview, users] = await Promise.all([
        callApi("/admin/overview?days=30"),
        callApi("/admin/users"),
    ]);
    return {
        overview: overview.ok ? overview.data : null,
        users: users.ok ? users.data : [],
        loadError: users.ok ? "" : users.error,
    };
}

const fmt = (n) => Number(n).toLocaleString("en-IN");

export default function AdminUsers() {
    const { overview, users, loadError } = useLoaderData();
    const [query, setQuery] = useState("");
    const currency = overview?.currency || "INR";
    const maxTokens = Math.max(1, ...users.map((u) => u.total_tokens));

    const q = query.trim().toLowerCase();
    const shown = q
        ? users.filter((u) => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q))
        : users;

    return (
        <Shell>
            <div className="page-head">
                <div>
                    <h1>Admin overview</h1>
                    <p className="muted">Everyone who signed up, their chatbots and what they have used.</p>
                </div>
            </div>

            {loadError && <p className="error">{loadError}</p>}

            {overview && (
                <div className="stat-grid">
                    <Stat icon={Users} label="Users" value={fmt(overview.users)} />
                    <Stat icon={Bot} label="Chatbots" value={fmt(overview.chatbots)} />
                    <Stat icon={Zap} label="Total tokens" value={fmt(overview.total_tokens)} sub="all time" />
                    <Stat icon={Wallet} label="Estimated bill" value={`${currency} ${fmt(overview.cost)}`} highlight />
                </div>
            )}

            <div className="section-head"><h2>Tokens, last 30 days</h2></div>
            <UsageChart daily={overview?.daily || []} />

            <div className="section-head">
                <h2>Users <span className="count-pill">{users.length}</span></h2>
                <label className="search">
                    <Search size={16} />
                    <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name or email" />
                </label>
            </div>

            {shown.length === 0 ? (
                <div className="empty-state"><p>{users.length === 0 ? "No users yet." : "No user matches your search."}</p></div>
            ) : (
                <div className="user-list">
                    <div className="user-row list-head">
                        <span>User</span><span className="hide-sm">Chatbots</span>
                        <span className="hide-sm">Tokens</span><span>Bill ({currency})</span><span />
                    </div>
                    {shown.map((u) => (
                        <Link key={u.id} to={`/admin/users/${u.id}`} className="user-row">
                            <div className="who">
                                <span className="avatar">{u.name.slice(0, 1).toUpperCase()}</span>
                                <div style={{ minWidth: 0 }}>
                                    <div className="who-name">{u.name}</div>
                                    <div className="who-sub">{u.email} &middot; joined {u.joined.slice(0, 10)}</div>
                                </div>
                            </div>
                            <div className="cell-num hide-sm">{fmt(u.chatbots)}</div>
                            <div className="hide-sm">
                                <span className="cell-num">{fmt(u.total_tokens)}</span>
                                <div className="meter"><span style={{ width: `${(u.total_tokens / maxTokens) * 100}%` }} /></div>
                            </div>
                            <div className="cell-num">{fmt(u.cost)}</div>
                            <ChevronRight size={18} className="chev" />
                        </Link>
                    ))}
                </div>
            )}
        </Shell>
    );
}