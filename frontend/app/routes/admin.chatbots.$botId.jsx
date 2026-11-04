import { Link, useLoaderData } from "@remix-run/react";
import { ArrowLeft, Globe, MessageSquare, Wallet, Zap } from "lucide-react";
import { callApi } from "../api.server";
import Shell from "../components/Shell";
import Stat from "../components/Stat";
import UsageChart from "../components/UsageChart";

export const meta = () => [{ title: "Admin - Chatbot" }];

export async function loader({ params }) {
    const result = await callApi(`/admin/chatbots/${params.botId}?days=30`);
    if (!result.ok) {
        throw new Response(result.error, { status: result.status });
    }
    return result.data;
}

const fmt = (n) => Number(n).toLocaleString("en-IN");

export default function AdminChatbot() {
    const { chatbot, owner, currency, daily } = useLoaderData();
    const total = chatbot.total_tokens || 1;
    const inPct = (chatbot.input_tokens / total) * 100;
    const outPct = (chatbot.output_tokens / total) * 100;

    return (
        <Shell>
            <Link to={`/admin/users/${owner.id}`} className="crumbs"><ArrowLeft size={16} /> {owner.name}</Link>

            <div className="profile">
                <span className="avatar lg">{chatbot.name.slice(0, 1).toUpperCase()}</span>
                <div>
                    <h1>{chatbot.name}</h1>
                    <p className="muted">
                        <span className="pill"><Globe size={12} /> {chatbot.domain}</span>
                        &nbsp; created {chatbot.created_at.slice(0, 10)}
                    </p>
                </div>
            </div>

            <div className="stat-grid">
                <Stat icon={MessageSquare} label="Questions" value={fmt(chatbot.requests)} />
                <Stat icon={Zap} label="Total tokens" value={fmt(chatbot.total_tokens)} />
                <Stat icon={Wallet} label="Estimated bill" value={`${currency} ${fmt(chatbot.cost)}`} highlight />
            </div>

            <div className="section-head"><h2>Input vs output tokens</h2></div>
            <div className="chart-card">
                <div className="split">
                    <span style={{ width: `${inPct}%` }} />
                    <span style={{ width: `${outPct}%` }} />
                </div>
                <div className="legend">
                    <span><i className="dot" style={{ background: "#d946ef" }} />Input (question + context): {fmt(chatbot.input_tokens)}</span>
                    <span><i className="dot" style={{ background: "#7c3aed" }} />Output (answer): {fmt(chatbot.output_tokens)}</span>
                </div>
            </div>

            <div className="section-head"><h2>Tokens, last 30 days</h2></div>
            <UsageChart daily={daily} />
        </Shell>
    );
}