import { useState } from "react";
import { Form, Link, useActionData, useNavigation } from "@remix-run/react";
import { redirect } from "@remix-run/node";
import { AlertCircle, Loader2, Upload } from "lucide-react";
import { callApi } from "../api.server";
import Shell from "../components/Shell";

export async function action({ request }) {
    const form = await request.formData();
    const name = String(form.get("name")|| "").trim();
    const domain = String(form.get("domain") || "").trim();
    const files = form.getAll("files").filter((f) => typeof f !== "string" && f.name);

    if(!name || !domain) {
        return { error: "Site name and domain are required."};
        }
    const created = await callApi("/sites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, domain }),
    });
    if (!created.ok) return { error: created.error };

    const siteId = created.data.id;
    const failed = [];
    for (const file of files) {
        const body = new FormData();
        body.append("file", file, file.name);
        const res = await callApi(`/sites/${siteId}/documents`, { method: "POST", body });
        if (!res.ok) failed.push(`${file.name}: ${res.error}`);
    }

    const note = failed.length ? `?uploadErrors=${encodeURIComponent(failed.join(" | "))}` : "";
    return redirect(`/sites/${siteId}${note}`);

}
export default function NewSite(){
    const actioData = useActionData();
    const navigation = useNavigation();
    const busy = navigation.state !== "idle";
    const [filenames, setFileNames] = useState([]);

    return (
        <Shell>
            <div className="form-page">
                <Link to="/dashboard" className="back-link">← Back to sites</Link>
                <h1> Add Website </h1>
                <p className="muted">
                     Give your website a name, tell us its domain, and upload the documents
          the chatbot should answer from. You'll get a token and a script to paste into the site.
                </p>
                <Form method="post" encType="multipart/form-data" className="dash-card form-card">
                <label className="field">
                    <span>Site name</span>
                    <input name="name" required maxLength={100} placeholder="Acme Support Bot" />
                </label>
                <label className="field">
                    <span>Website domain</span>
                    <input name="domain" required placeholder="acme.com"/>
                    <small className="muted">
                       The chatbot only works on this domain. Use "localhost" while testing. 
                    </small>
                </label>
                <div className="field">
                    <span>Document</span>
                    <label className={`dropzone${busy ? " busy" : ""}`}>
                        <input type="file" name="files" multiple accept=".pdf,.docx, .txt" disabled={busy} onChange={(e) => setFileNames(Array.from(e.target.files).map((f) => f.name))} />
                        <div className="dz-icon"><Upload size={24}/></div>
                        <div className="dz-title">Choose file or <span>browse</span></div>
                        <div className="dz-hint">PDF, DOCX or TXT, up to 10 MB each. you can add more later.</div>
                    </label>
                    {filenames.length > 0 && (
                        <ul className="picked-files">
                            {filenames.map((n) => <li key={n}>{n}</li>)}
                        </ul>
                    )}
                </div>
                {actioData?.error && (
                    <p className="error"><AlertCircle size={16}/>{actioData.error}</p>
                )}
                <button type="submit" className="btn btn-primary" disabled={busy}>
                    {busy ? (
                        <><Loader2 size={16} className="spin"/> Creating... processing documents can take a moment</>
                    ) : (
                        "Create chatbot"
                    )}
                </button>
                </Form>
            </div>
        </Shell>
    );
}
    
