import { useEffect, useRef, useState } from "react";
import { useFetcher } from "@remix-run/react";
import { AlertCircle, FileText,Globe, Link2, Loader2, Trash2, Upload } from "lucide-react";

const ALLOWED = [".pdf", ".docx", ".txt"];
const MAX_MB = 10;

export default function SiteDocuments({ documents, loadError }) {
    const uploader = useFetcher();
    const remover = useFetcher();
    const linker = useFetcher();
    const linkFormRef = useRef(null);
    const linking = linker.state !== "idle";
    const linkError = linker.data && !linker.data.ok ? linker.data.error : "";
    const formRef = useRef(null);
    const [localError, setLocalError] = useState("");

    const uploading = uploader.state !== "idle";
    const uploadError = uploader.data && !uploader.data.ok ? uploader.data.error : "";
    const removeError = remover.data && !remover.data.ok ? remover.data.error : "";
    const deletingId = remover.state !== "idle" ? remover.formData?.get("document_id") : null;
     useEffect(() => {
        if (linker.state === "idle" && linker.data?.ok) linkFormRef.current?.reset();
    }, [linker.state, linker.data]);

    function handleChange(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;

        const bad = files.find(
            (f) => !ALLOWED.some((ext) => f.name.toLowerCase().endsWith(ext)) || f.size > MAX_MB * 1024 * 1024
        );
        if (bad) {
            setLocalError(`"${bad.name}" must be a PDF, DOCX or TXT file under ${MAX_MB} MB.`);
            event.target.value = "";
            return;
        }
        setLocalError("");
        uploader.submit(formRef.current);
    }
    useEffect(() => {
        if (uploader.state === "idle" && uploader.data) formRef.current?.reset();
    }, [uploader.state, uploader.data]);

    return (
        <>
           <uploader.Form method="post" encType="multipart/form-data" ref={formRef} className="docs-upload">
             <input type="hidden" name="intent" value="upload"/>
             <label className={`dropzone compact${uploading ? " busy" : ""}`}>
                <input type="file" name="files" multiple accept=".pdf,.docx,.txt" onChange={handleChange} disabled={uploading}/>
                <div className="dz-icon">
                    {uploading ? <Loader2 size={22} className="spin"/> : <Upload size={22}/>}
                </div>
                {uploading ? (
                    <>
                      <div className="dz-title">Processing your documents...</div>
                      <div className="dz-hint">This can take a few seconds.</div>
                    </>
                    ) : (
                        <>
                           <div className="dz-title">Add document or <span>browse</span></div>
                           <div className="dz-hint">PDF, DOCX or TXT, up to {MAX_MB} MB each</div>
                        </>
                    )}
             </label>
             {(localError || uploadError) && (
                <p className="error"><AlertCircle size={16}/> {localError || uploadError}</p>
             )}
           </uploader.Form>
            <linker.Form method="post" ref={linkFormRef} className="link-form">
             <input type="hidden" name="intent" value="add-url"/>
             <div className="link-row">
                <div className="link-input">
                    <Link2 size={16}/>
                    <input
                        type="url"
                        name="url"
                        placeholder="https://yourcompany.com/about"
                        required
                        disabled={linking}
                    />
                </div>
                <button type="submit" className="btn btn-primary" disabled={linking}>
                    {linking ? <Loader2 size={16} className="spin"/> : "Add link"}
                </button>
             </div>
             <label className="link-crawl">
                <input type="checkbox" name="crawl" disabled={linking}/>
                Crawl the whole site (up to 15 pages)
             </label>
             {linkError && <p className="error"><AlertCircle size={16}/> {linkError}</p>}
           </linker.Form>

           {loadError && <p className="error"><AlertCircle size={16}/>{loadError}</p>}

           {documents.length === 0 ? (
             <div className="empty-state">No document yet. Upload one above so the chatbot has something to answer from.</div>
           ) : (
            <ul className="doc-list">
                {documents.map((doc) => {
                    const type = doc.file_type.toLowerCase();
                    const deleting = deletingId === doc.document_id;
                    return (
                        <li key={doc.document_id} className="doc-card">
                            <div className="doc-main plain">
                                <span className={`file-badge ${type}`}><FileText size={20}/></span>
                                <span className="doc-info">
                                    <span className="doc-name" title={doc.filename}>{doc.filename}</span>
                                    <span className="doc-meta">
                                        {type.toUpperCase()} · {doc.chunk_count} chunks · {Math.max(1, Math.round(doc.size_bytes / 1024))} KB
                                    </span>
                                </span>
                            </div>
                            <remover.Form method="post" onSubmit={(e) => {if (!window.confirm(`Delete "${doc.filename}"?`)) e.preventDefault();
                            }}
                            >
                                <input type="hidden" name="intent" value="delete-doc"/>
                                <input type="hidden" name="document_id" value={doc.document_id}/>
                                <button type="submit" className="icon-btn" disabled={deleting} aria-label={`Delete ${doc.filename}`} title="Delete">
                                    {deleting ? <Loader2 size={18} className="spin" /> : <Trash2 size={18}/>}
                                </button>
                            </remover.Form>
                        </li>
                    )
                })}
            </ul>
           )}
           {removeError && <p className="error"><AlertCircle size={16}/> {removeError}</p>}
        </>
    );
}