import { Link, useFetcher, useLoaderData, useSearchParams } from "@remix-run/react";
import { redirect } from "@remix-run/node";
import { AlertCircle, Globe, Key, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { callApi } from "../api.server";
import Shell from "../components/Shell";
import CopyButton from "../components/CopyButton";
import SiteDocuments from "../components/SiteDocuments";

export const meta = ({ data }) => [
    { title: data?.site ? `${data.site.name} · chatbot` : "Website" },
];
export async function loader({ params }) {
    const base = `/sites/${params.siteId}`;
    const site = await callApi(base);
    if (!site.ok) {
        const missing = site.status === 404 || site.status === 422;
        throw new Response(missing ? "Site not found." : site.error, {
            status: missing ? 404 : 502,
        });
    }
    const docs = await callApi(`${base}/documents`);
    return {
        site: site.data,
        documents: docs.ok ? docs.data : [],
        docsError: docs.ok ? "" : docs.error,
    };
}

export async function action({request, params}) {
    const form = await request.formData();
    const intent = String(form.get("intent") || "");
    const base = `/sites/${params.siteId}`;

    if (intent === "rotate") {
        const res = await callApi(`${base}/rotate`, { method: "POST" });
        return res.ok ? { ok:true } : { ok: false, error: res.error };
    }
    if (intent === "delete-site") {
        const res = await callApi(base, {method: "DELETE" });
        if(!res.ok) return {ok:false, error: res.error};
        return redirect("/dashboard"); 
    }
    if (intent === "upload") {
        const files = form.getAll("files").filter((f) => typeof f !== "string" && f.name);
        if(files.length === 0) return {ok:false, error: "Choose a file first." };

        const failed = [];
        for (const file of files) {
            const body = new FormData();
            body.append("file", file, file.name);
            const res = await callApi(`${base}/documents`, { method: "POST", body });
            if (!res.ok) failed.push(`${file.name}: ${res.error}`);
        }
        return failed.length ? { ok: false, error: failed.join(" | ")} : { ok: true };
    }
    if(intent === "delete-doc") {
        const id = String(form.get("document_id") || "");
        const res = await callApi(`${base}/documents/${encodeURIComponent(id)}`, { method: "DELETE" });
        return res.ok ? { ok:true } : { ok:false, error: res.error};
    }
    return { ok: false, error: " Unknown action. "};
    
}
export default function SitePage() {
    const { site, documents, docsError } = useLoaderData();
    const [params] = useSearchParams();
    const uploadErrors = params.get("uploadErrors");

    const rotator = useFetcher();
    const deleter = useFetcher();
    const rotating = rotator.state !== "idle";
    const deleting = deleter.state !== "idle";
    const rotateError = rotator.data && !rotator.data.ok ? rotator.data.error : "";
    const deleteError = deleter.data && !deleter.data.ok ? deleter.data.error : "";


    return(
        <Shell>
            <div className="site-head">
                <div>
                    <Link to="/dashboard" className="back-link">← Back to sites</Link>
                    <h1>{site.name}</h1>
                    <span className="site-domain"><Globe size={14}/>{site.domain}</span>
                </div>
                <deleter.Form method="post" onSubmit={(e) => {if (!window.confirm(`Delete "${site.name}" and all its documents?`)) e.preventDefault();
                }}
                >
                    <input type="hidden" name="intent" value="delete-site"/>
                    <button type="submit" className="btn btn-danger" disabled={deleting}>
                        {deleting ? <Loader2 size={16} className="spin"/> : <Trash2 size={16}/>}
                        Delete site
                    </button>
                </deleter.Form>
            </div>

            {deleteError && <p className="error"><AlertCircle size={16}/> {deleteError}</p>}
            {uploadErrors && (
                <div className="warn">
                    <AlertCircle size={16}/>
                    <span>Site create, but some document failed: {uploadErrors}</span>
                </div>
            )}
            <div className="detail-grid">
                <section className="dash-card">
                    <h2>
                        <span><Key size={16}/> 1. your token</span>
                        <rotator.Form method="post" onSubmit={(e) => { if (!window.confirm("Rotate the token? The script already pasted on your websitte will stop working until you replace it.")){
                            e.preventDefault();
                        }
                    }}
                    >
                        <input type="hidden" name="intent" value="rotate"/>
                        <button type="submit" className="btn btn-ghost" disabled={rotating}>
                            {rotating ? <Loader2 size={14} className="spin"/> : <RefreshCw size={14}/>}
                            Rotate
                        </button>
                    </rotator.Form>
                    </h2>
                    <p className="muted">The widget sends this token with every chat message. It only works on {site.domain}.</p>
                    <div className="code-row">
                        <pre className="code-block">{site.token}</pre>
                        <CopyButton value={site.token}/>
                    </div>
                    {rotateError && <p className="error"><AlertCircle size={16}/>{rotateError}</p>}
                </section>
                <section className="dash-card">
                    <h2><span>2. Embed script</span></h2>
                    <p className="muted">
                        Paste this into the <code>&lt;head&gt;</code> of {site.domain}. A chat bubble
                        appears at the bottom-right of the site.
                    </p>
                    <div className="code-row">
                        <pre className="code-block snippet">{site.snippet}</pre>
                        <CopyButton value={site.snippet} label="Copy script" />
                    </div>
                </section>
                <section className="dash-card">
                    <h2>
                        <span>3. Documents</span>
                        <span className="count-pill">{documents.length}</span>
                    </h2>
                    <p className="muted">The chatbot answer only from these documents.</p>
                    <SiteDocuments documents={documents} loadError={docsError} />
                </section>
            </div>
        </Shell>
    );
}