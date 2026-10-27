import { Link, useLoaderData } from "@remix-run/react";
import { Globe, Plus } from "lucide-react";
import { callApi } from "../api.server";
import Shell from "../components/Shell";

export const meta = () => [{ title: "your website" }];

export async function loader() {
    const result = await callApi("/sites");
    return {
        sites: result.ok ? result.data : [],
        loadError: result.ok ? "" : result.error,
    }; 
}

export default function Dashboard(){
    const { sites, loadError } = useLoaderData();
    
    return (
        <Shell>
            <div className="page-head">
                <div>
                    <h1>Your Websites</h1>
                    <p className="muted">Each website gets its own chatbot, token and embed script.</p>
                </div>
                <Link to="/sites/new" className="btn btn-primary">
                 <Plus size={16}/> Add website
                </Link>
            </div>

            {loadError && <p className="error">{loadError}</p>}
            {sites.length === 0 && !loadError ? (
                <div className="empty-state">
                    <p><strong>No website yet</strong></p>
                    <p>Add a website, uplode its document, and get a script to paste into its header.</p>
                    <Link to="/sites/new" className="btn btn-primary">Add your first website</Link>
                </div>
                ) :(
                    <div className="site-grid">
                        {sites.map((site) =>(
                            <Link key={site.id} to={`/sites/${site.id}`} className="site-card">
                                <h3>{site.name}</h3>
                                <span className="site-domain"><Globe size={14}/>{site.domain}</span>
                                <p className="site-meta">Create {site.created_at.slice(0, 10)}</p>
                            </Link>
                        ))}
                    </div>
                )}
        </Shell>
    );
}