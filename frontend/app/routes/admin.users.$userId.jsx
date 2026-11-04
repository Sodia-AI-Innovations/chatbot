import { Link, useLoaderData } from "@remix-run/react";
import { ArrowLeft, Bot, Clock, Globe, Wallet, Zap } from "lucide-react";
import { callApi } from "../api.server";
import Shell from "../components/Shell";
import Stat from "../components/Stat";

export const meta = () => [{ title: "Admin - User" }];

export async function loader({ params }) {
    const result = await callApi(`/admin/users/${params.userId}`);
    if (!result.ok) {
        throw new Response(result.error, { status: result.status });
    }
    return result.data;
}

const fmt = (n) => Number(n).toLocaleString("en-IN");

export default function AdminUser() {
    const { user, chatbots, direct_tokens, total_tokens, cost, currency } = useLoaderData();
    const maxTokens = Math.max(1, ...chatbots.map((b) => b.total_tokens));

    return (
        <Shell>
            <Link to="/admin" className="crumbs"><ArrowLeft size={16} /> All users</Link>

            <div className="profile">
                <span className="avatar lg">{user.name.slice(0, 1).toUpperCase()}</span>
                <div>
                    <h1>{user.name}</h1>
                    <p className="muted">{user.email} &middot; joined {user.joined.slice(0, 10)}</p>
                </div>
            </div>

            <div className="stat-grid">
                <Stat icon={Bot} label="Chatbots" value={fmt(chatbots.length)} />
                <Stat icon={Zap} label="Total tokens" value={fmt(total_tokens)} />
                <Stat icon={Wallet} label="Estimated bill" value={`${currency} ${fmt(cost)}`} highlight />
            </div>

            <div className="section-head">
                <h2>Chatbots <span className="count-pill">{chatbots.length}</span></h2>
            </div>

            {chatbots.length === 0 ? (
                <div className="empty-state"><p>This user has not created a chatbot yet.</p></div>
            ) : (
                <div className="bot-grid">
                    {chatbots.map((b) => (
                        <Link key={b.id} to={`/admin/chatbots/${b.id}`} className="bot-card">
                            <div className="bot-top">
                                <span className="stat-icon"><Bot size={20} /></span>
                                <div>
                                    <h3>{b.name}</h3>
                                    <span className="site-domain"><Globe size={13} /> {b.domain}</span>
                                </div>
                            </div>
                            <div className="bot-nums">
                                <p><strong>{fmt(b.requests)}</strong>Questions</p>
                                <p><strong>{fmt(b.total_tokens)}</strong>Tokens</p>
                                <p><strong>{fmt(b.cost)}</strong>{currency}</p>
                            </div>
                            <div className="meter"><span style={{ width: `${(b.total_tokens / maxTokens) * 100}%` }} /></div>
                            <p className="bot-foot">
                                <Clock size={13} />
                                {b.last_active ? `Last active ${b.last_active.slice(0, 16).replace("T", " ")}` : "No activity yet"}
                            </p>
                        </Link>
                    ))}
                </div>
            )}

            {direct_tokens > 0 && (
                <p className="muted" style={{ marginTop: 14 }}>
                    Plus {fmt(direct_tokens)} tokens from chats not tied to a chatbot.
                </p>
            )}
        </Shell>
    );
}