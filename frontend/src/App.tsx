import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

type Page =
  | "Dashboard"
  | "Transactions"
  | "Budgets"
  | "Smart Insights"
  | "Goals"
  | "AI Assistant"
  | "Agent Memory"
  | "Settings";

const nav: { label: Page; icon: string }[] = [
  { label: "Dashboard", icon: "space_dashboard" },
  { label: "Transactions", icon: "receipt_long" },
  { label: "Budgets", icon: "account_balance_wallet" },
  { label: "Smart Insights", icon: "auto_awesome" },
  { label: "Goals", icon: "flag" },
  { label: "AI Assistant", icon: "chat_bubble" },
  { label: "Agent Memory", icon: "database" },
  { label: "Settings", icon: "settings" },
];

const pageCopy: Record<Page, string> = {
  Dashboard: "Your finances, clearly understood.",
  Transactions: "Review and manage every expense.",
  Budgets: "Set limits that keep spending intentional.",
  "Smart Insights": "Forward-looking guidance for better decisions.",
  Goals: "Build toward what matters.",
  "AI Assistant": "Ask questions about your financial life.",
  "Agent Memory": "Review what your assistant remembers.",
  Settings: "Configure your data and AI connections.",
};

const API_BASE = "/api";

function Icon({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  return <span className={`material-symbols-rounded icon-${size}`} aria-hidden="true">{name}</span>;
}

function Button({ children, variant = "primary", onClick, type = "button", disabled }: { children: ReactNode; variant?: "primary" | "secondary" | "danger" | "ghost"; onClick?: () => void; type?: "button" | "submit"; disabled?: boolean; }) {
  return <button className={`button button-${variant}`} onClick={onClick} type={type} disabled={disabled}>{children}</button>;
}

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`card ${className}`}>{children}</section>;
}

function SectionTitle({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) {
  return (
    <div className="section-title">
      <div>
        <h2>{title}</h2>
        {detail && <p>{detail}</p>}
      </div>
      {action}
    </div>
  );
}

function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "danger" | "indigo" | "warning" }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

function KPI({ label, value, detail, icon }: { label: string; value: string; detail: string; icon?: string }) {
  return (
    <Card className="kpi">
      <div className="kpi-top"><span className="eyebrow">{label}</span>{icon && <Icon name={icon} />}</div>
      <strong className="metric">{value}</strong>
      <span className="detail">{detail}</span>
    </Card>
  );
}

function Progress({ value, over = false }: { value: number; over?: boolean }) {
  return <div className="progress"><span className={over ? "over" : ""} style={{ width: `${Math.min(value, 100)}%` }} /></div>;
}

function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: ReactNode }) {
  return <label className="field"><span>{label}</span>{hint}{children}</label>;
}

function Modal({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-head"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close"><Icon name="close" /></button></div>
        {children}
      </div>
    </div>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="empty-state"><Icon name="inbox" /><strong>{title}</strong><span>{detail}</span></div>;
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------
const TOKEN_KEY = "auth_token";
function getToken(): string | null { return localStorage.getItem(TOKEN_KEY); }
function setToken(t: string | null) { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); }

async function api(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(options.headers as any) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth screen
// ---------------------------------------------------------------------------
function AuthScreen({ onAuth }: { onAuth: (token: string) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await api("/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name: name }) });
      }
      const data = await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setToken(data.access_token);
      onAuth(data.access_token);
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <Card className="auth-card">
        <div className="brand"><div><span className="brand-mark"><i /></span><strong>Expense Tracker</strong></div><small>AI Agent · AIDE3313</small></div>
        <h2>{mode === "login" ? "Sign in" : "Create account"}</h2>
        <p className="auth-sub">{mode === "login" ? "Access your financial dashboard." : "Start tracking your expenses."}</p>
        <form className="form-stack" onSubmit={submit}>
          {mode === "register" && <Field label="Full name"><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" /></Field>}
          <Field label="Email"><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required /></Field>
          <Field label="Password"><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required minLength={6} /></Field>
          {error && <div className="alert"><div className="alert-icon"><Icon name="error" /></div><div><strong>{error}</strong></div></div>}
          <Button type="submit" disabled={loading}>{loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</Button>
        </form>
        <button className="link-btn" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
          {mode === "login" ? "No account? Register" : "Already have an account? Sign in"}
        </button>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard (real data)
// ---------------------------------------------------------------------------
function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const month = new Date().toISOString().slice(0, 7);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const summary = await api(`/dashboard/summary?month=${month}`);
      setData(summary);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <div className="page-grid"><Card className="span-12"><EmptyState title="Loading" detail="Fetching your financial summary…" /></Card></div>;
  if (error) return <div className="page-grid"><Card className="span-12"><div className="alert"><div className="alert-icon"><Icon name="error" /></div><div><strong>{error}</strong><p>Could not load dashboard.</p></div></div><Button onClick={load}>Retry</Button></Card></div>;

  const income = data?.income ?? 0;
  const expenses = data?.expenses ?? 0;
  const net = data?.net ?? 0;

  return (
    <div className="page-grid">
      <div className="kpi-grid span-12">
        <KPI label="Income this month" value={`Rs. ${income.toLocaleString()}`} detail="From your transactions" icon="trending_up" />
        <KPI label="Expenses this month" value={`Rs. ${expenses.toLocaleString()}`} detail="From your transactions" icon="trending_down" />
        <KPI label="Net cash flow" value={`Rs. ${net.toLocaleString()}`} detail={net >= 0 ? "Positive" : "Negative"} icon="account_balance" />
        <KPI label="Budgets" value={String((data?.budgets ?? []).length)} detail="Active budgets" icon="account_balance_wallet" />
      </div>
      <Card className="span-12">
        <SectionTitle title="Getting started" detail="Your data is loaded from the backend" />
        {expenses === 0 && income === 0 ? (
          <EmptyState title="No transactions yet" detail="Add your first transaction to see charts and insights." />
        ) : (
          <p style={{ color: "var(--text-muted)", fontSize: 12 }}>Charts will populate as you add transactions. Budgets: {(data?.budgets ?? []).length}.</p>
        )}
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Transactions (real data)
// ---------------------------------------------------------------------------
function Transactions() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [desc, setDesc] = useState("");
  const [amount, setAmount] = useState("");
  const [cat, setCat] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api("/expenses");
      setRows(data || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const add = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/expenses", { method: "POST", body: JSON.stringify({ amount: Number(amount), description: desc, category_id: null }) });
      setOpen(false);
      setDesc(""); setAmount(""); setCat("");
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Delete this transaction?")) return;
    try {
      await api(`/expenses/${id}`, { method: "DELETE" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="page-stack">
      <div className="page-actions"><span>All amounts in your selected currency.</span><Button onClick={() => setOpen(true)}><Icon name="add" size="sm" /> Add expense</Button></div>
      {error && <div className="alert"><div className="alert-icon"><Icon name="error" /></div><div><strong>{error}</strong></div></div>}
      {loading ? (
        <Card><EmptyState title="Loading" detail="Fetching transactions…" /></Card>
      ) : rows.length === 0 ? (
        <Card><EmptyState title="No transactions yet" detail="Add your first transaction to get started." /></Card>
      ) : (
        <div className="table-shell">
          <table>
            <thead><tr><th>Description</th><th>Category</th><th>Date</th><th>Amount</th><th></th></tr></thead>
            <tbody>
              {rows.map((r: any) => (
                <tr key={r.id}>
                  <td><strong>{r.description || "—"}</strong></td>
                  <td>{r.category?.name || "—"}</td>
                  <td>{new Date(r.date).toLocaleDateString()}</td>
                  <td className="money">{Number(r.amount).toLocaleString()}</td>
                  <td><button className="icon-button" onClick={() => remove(r.id)}><Icon name="delete" size="sm" /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && <Modal title="Add expense" onClose={() => setOpen(false)}>
        <form className="form-stack" onSubmit={add}>
          <Field label="Description"><input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="e.g. Lunch" required /></Field>
          <Field label="Amount"><input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0" required /></Field>
          <div className="modal-actions"><Button variant="secondary" onClick={() => setOpen(false)}>Cancel</Button><Button type="submit">Save expense</Button></div>
        </form>
      </Modal>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Other pages (placeholders wired to backend later)
// ---------------------------------------------------------------------------
function SimplePage({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="page-stack">
      <Card><SectionTitle title={title} detail={detail} /><EmptyState title="Coming soon" detail="This section will be wired to the backend." /></Card>
    </div>
  );
}

function Budgets() { return <SimplePage title="Budgets" detail="Set limits that keep spending intentional." />; }
function SmartInsights() { return <SimplePage title="Smart Insights" detail="Forward-looking guidance for better decisions." />; }
function Goals() { return <SimplePage title="Goals" detail="Build toward what matters." />; }
function AIAssistant() { return <SimplePage title="AI Assistant" detail="Ask questions about your financial life." />; }
function AgentMemory() { return <SimplePage title="Agent Memory" detail="Review what your assistant remembers." />; }
function Settings() { return <SimplePage title="Settings" detail="Configure your data and AI connections." />; }

const pages: Record<Page, () => ReactNode> = {
  Dashboard,
  Transactions,
  Budgets,
  "Smart Insights": SmartInsights,
  Goals,
  "AI Assistant": AIAssistant,
  "Agent Memory": AgentMemory,
  Settings,
};

export default function App() {
  const [token, setToken] = useState<string | null>(getToken());
  const [page, setPage] = useState<Page>("Dashboard");
  const [drawer, setDrawer] = useState(false);
  const PageContent = useMemo(() => pages[page], [page]);
  const navigate = (next: Page) => { setPage(next); setDrawer(false); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const logout = () => { setToken(null); setToken(null); };

  if (!token) {
    return <AuthScreen onAuth={setToken} />;
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${drawer ? "drawer-open" : ""}`}>
        <div className="brand"><div><span className="brand-mark"><i /></span><strong>Expense Tracker</strong></div><small>AI Agent · AIDE3313</small></div>
        <div className="workspace-switcher">
          <span className="workspace-avatar">U</span>
          <div><small>Workspace</small><strong>Personal finances</strong></div>
          <Icon name="unfold_more" size="sm" />
        </div>
        <span className="nav-label">Product</span>
        <nav>{nav.map((item) => <button className={page === item.label ? "active" : ""} onClick={() => navigate(item.label)} key={item.label}><Icon name={item.icon} /><span>{item.label}</span>{page === item.label && <i />}</button>)}</nav>
        <div className="sidebar-foot"><div className="avatar">U</div><div><strong>User</strong><span>Personal workspace</span></div><button className="icon-button" onClick={() => { setToken(null); }} aria-label="Logout"><Icon name="logout" size="sm" /></button></div>
      </aside>
      {drawer && <div className="drawer-scrim" onClick={() => setDrawer(false)} />}
      <main>
        <header className="topbar">
          <button className="menu-button" onClick={() => setDrawer(true)}><Icon name="menu" /></button>
          <div><h1>{page}</h1><p>{pageCopy[page]}</p></div>
          <div className="topbar-actions">
            <button className="header-action" aria-label="Search"><Icon name="search" /></button>
            <button className="header-action notification-action" aria-label="Notifications"><Icon name="notifications" /><i /></button>
            <div className="connection"><span className="status-dot" /><span>Connected</span></div>
          </div>
        </header>
        <div className="content" key={page}><PageContent /></div>
      </main>
    </div>
  );
}
PY