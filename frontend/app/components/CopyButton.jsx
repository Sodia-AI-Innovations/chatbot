import { useState } from "react";
import { Check, Copy } from "lucide-react";

export default function CopyButton({ value, label = "copy"}) {
    const [copied, setCopied] = useState(false);

    async function copy() {
        try {
            await navigator.clipboard.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 1200);
        }catch {

        }
        
    }
    return (
        <button type="button" className="btn btn-ghost" onClick={copy}>
            {copied ? <Check size={14} /> : <Copy size={14}/>}
            {copied ? "Copied!" : label}
        </button>
    )
}