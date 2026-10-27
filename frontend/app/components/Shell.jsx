import { Link, NavLink } from "@remix-run/react";
import { Bot, Plus } from "lucide-react";

export default function Shell({ children }) {
    return (
        <div className="shell">
            <header className="shell-header">
                <div className="shell-inner">
                    <Link to="/dashboard" className="brand">
                     <span className="brand-icon"><Bot size={18}/></span>
                     Site Chatbot
                    </Link>
                    <nav className="shell-nav">
                        <NavLink to="/dashboard" className="nav-link">Sites</NavLink>
                        <Link to="/sites/new" className="btn btn-primary">
                          <Plus size={16} /> New site
                        </Link>
                    </nav>
                </div>
            </header>
            <main className="shell-main">{children}</main>
        </div>
    );
}