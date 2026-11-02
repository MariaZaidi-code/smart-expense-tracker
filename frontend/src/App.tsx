import { FormEvent, ReactNode, useMemo, useState } from "react";

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

const transactions = [
  ["Broadway Pizza", "Food & dining", "Nov 29, 2026", "HBL Debit •• 1842", "Rs. 1,450", "Review"],
  ["Careem", "Transport", "Nov 28, 2026", "JazzCash", "Rs. 620", "Within budget"],
  ["Netflix", "Entertainment", "Nov 27, 2026", "HBL Debit •• 1842", "Rs. 1,100", "Within budget"],
  ["Naheed Supermarket", "Groceries", "Nov 26, 2026", "Cash", "Rs. 2,480", "Within budget"],
  ["StormFiber", "Utilities", "Nov 25, 2026", "Bank transfer", "Rs. 2,200", "Within budget"],
];

const budgets = [
  ["Food & dining", 1450, 8000, "18%", "On track"],
  ["Groceries", 2480, 7000, "35%", "On track"],
  ["Transport", 620, 5000, "12%", "On track"],
  ["Entertainment", 1100, 3000, "37%", "Watch"],
  ["Utilities", 2200, 6000, "37%", "On track"],
  ["Shopping", 0, 7000, "0%", "On track"],
  ["Health", 0, 4000, "0%", "On track"],
];

function Icon({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  return <span className={`material-symbols-rounded icon-${size}`} aria-hidden="true">{name}</span>;
}

function Button({
  children,
  variant = "primary",
  onClick,
  type = "button",
  disabled,
}: {
  children: ReactNode;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
}) {
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

function Hero() {
  return (
    <section className="hero">
      <span className="eyebrow hero-eyebrow">Remaining budget</span>
      <strong>Rs. 38,150</strong>
      <span className="hero-change"><Icon name="trending_down" size="sm" /> 12.4% lower than last month</span>
      <div className="hero-foot"><span>November 2026</span><span>83% available</span></div>
    </section>
  );
}

function SpendingChart() {
  const bars = [30, 44, 22, 52, 35, 63, 45, 33, 58, 71, 43, 65, 52, 79, 44, 55, 38, 69, 48, 61, 73, 46, 58, 67, 52, 76, 62, 48, 70, 86];
  const points = bars.map((bar, i) => `${i * (580 / 29)},${126 - bar}`).join(" ");
  return (
    <div className="chart-wrap">
      <div className="chart-meta"><span>Nov 1</span><span className="chart-total">Rs. 7,850 total</span></div>
      <svg viewBox="0 0 580 150" className="activity-chart" role="img" aria-label="Daily spending activity">
        {[25, 65, 105].map((y) => <line key={y} x1="0" y1={y} x2="580" y2={y} className="grid-line" />)}
        {bars.map((bar, i) => <rect key={i} x={i * 20 - 4} y={145 - bar * .65} width="8" height={bar * .65} rx="2" className={i === 29 ? "bar-last" : "bar"} />)}
        <polyline points={points} transform="translate(0 8)" className="area-line" />
        <circle cx="580" cy={134 - bars[29]} r="4" className="line-dot" />
      </svg>
      <div className="chart-axis"><span>Nov 1</span><span>Nov 8</span><span>Nov 15</span><span>Nov 22</span><span>Nov 30</span></div>
    </div>
  );
}

function Donut() {
  return (
    <div className="donut-layout">
      <div className="donut" aria-label="Category breakdown chart">
        <div><strong>Rs. 7,850</strong><span>Total spent</span></div>
      </div>
      <div className="legend">
        {[
          ["Groceries", "Rs. 2,480", "c1"],
          ["Utilities", "Rs. 2,200", "c2"],
          ["Food & dining", "Rs. 1,450", "c3"],
          ["Entertainment", "Rs. 1,100", "c4"],
          ["Transport", "Rs. 620", "c5"],
        ].map(([name, value, color]) => <div key={name}><span className={`dot ${color}`} /><span>{name}</span><strong>{value}</strong></div>)}
      </div>
    </div>
  );
}

function BudgetList({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`budget-list ${compact ? "compact" : ""}`}>
      {budgets.map(([name, spent, limit, percentage, status]) => (
        <div className="budget-row" key={name as string}>
          <div className="budget-info"><strong>{name}</strong><span>Rs. {(spent as number).toLocaleString()} / Rs. {(limit as number).toLocaleString()}</span></div>
          <Progress value={(spent as number) / (limit as number) * 100} />
          <Pill tone={status === "Watch" ? "warning" : "neutral"}>{status}</Pill>
        </div>
      ))}
    </div>
  );
}

function TransactionTable({ all = false }: { all?: boolean }) {
  const rows = all ? [...transactions, ["K-Electric", "Utilities", "Nov 19, 2026", "Bank transfer", "Rs. 0", "Pending"], ["Daraz", "Shopping", "Nov 14, 2026", "HBL Debit •• 1842", "Rs. 0", "Within budget"]] : transactions;
  return (
    <div className="table-shell">
      <table>
        <thead><tr><th>Description</th><th>Category</th><th>Date</th><th>Payment</th><th className="align-right">Amount</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={`${row[0]}${row[2]}`}><td><div className="merchant"><span>{row[0].slice(0, 1)}</span><div><strong>{row[0]}</strong><small>{row[5]}</small></div></div></td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td className="align-right money">{row[4]}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

function Dashboard() {
  return (
    <div className="page-grid">
      <Hero />
      <div className="kpi-grid span-12">
        <KPI label="Safe to spend" value="Rs. 35,200" detail="Rs. 1,214/day · Comfortable" icon="shield" />
        <KPI label="Spent this month" value="Rs. 7,850" detail="Across all categories" icon="payments" />
        <KPI label="Total budget" value="Rs. 46,000" detail="Monthly limit" icon="account_balance_wallet" />
        <KPI label="Vs. last month" value="+12.3%" detail="Spending increased" icon="trending_up" />
      </div>
      <Card className="span-8"><SectionTitle title="Spending activity" detail="Daily spend across November" /><SpendingChart /></Card>
      <Card className="span-4"><SectionTitle title="Category breakdown" detail="Share of monthly spending" /><Donut /></Card>
      <Card className="span-7"><SectionTitle title="Budget progress" detail="7 active category budgets" /><BudgetList compact /></Card>
      <Card className="span-5">
        <SectionTitle title="Unusual spending" detail="Items that differ from your normal pattern" />
        <div className="alert"><div className="alert-icon"><Icon name="priority_high" /></div><div><strong>Dining expense is higher than usual</strong><p>Broadway Pizza was 68% above your typical dining transaction.</p><span>Nov 29 · Rs. 1,450</span></div></div>
        <div className="empty-state"><Icon name="check_circle" /><strong>No other unusual activity</strong><span>Your remaining transactions look normal.</span></div>
      </Card>
      <Card className="span-12"><SectionTitle title="Recent transactions" detail="Your latest account activity" action={<Button variant="secondary">View all <Icon name="arrow_forward" size="sm" /></Button>} /><TransactionTable /></Card>
    </div>
  );
}

function ExpenseForm({ onClose }: { onClose: () => void }) {
  const [description, setDescription] = useState("");
  const suggestion = /net|cinema|spotify|game/i.test(description) ? "Entertainment" : /careem|indrive|fuel/i.test(description) ? "Transport" : /mart|store|grocery/i.test(description) ? "Groceries" : "Food & dining";
  return (
    <form className="form-stack" onSubmit={(event) => { event.preventDefault(); onClose(); }}>
      <div className="form-grid">
        <Field label="Description"><input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Netflix" autoFocus /></Field>
        <Field label="Amount"><div className="input-prefix"><span>Rs.</span><input type="number" placeholder="0" /></div></Field>
      </div>
      <Field label="Category" hint={<span className="suggestion"><Icon name="auto_awesome" size="sm" /> Suggested {suggestion} — keyword heuristic (45% confidence)</span>}>
        <select value={suggestion} onChange={() => undefined}><option>{suggestion}</option><option>Utilities</option><option>Shopping</option></select>
      </Field>
      <div className="form-grid">
        <Field label="Date"><input type="date" defaultValue="2026-11-30" /></Field>
        <Field label="Payment method"><select defaultValue="HBL"><option value="HBL">HBL Debit •• 1842</option><option>Cash</option><option>JazzCash</option></select></Field>
      </div>
      <Field label="Notes"><textarea placeholder="Optional context for this expense" rows={3} /></Field>
      <div className="modal-actions"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit">Save expense</Button></div>
    </form>
  );
}

function Transactions() {
  const [open, setOpen] = useState(false);
  return (
    <div className="page-stack">
      <div className="page-actions"><span>All amounts are shown in Pakistani Rupees.</span><Button onClick={() => setOpen(true)}><Icon name="add" size="sm" /> Add expense</Button></div>
      <Card className="filter-card">
        <div className="search"><Icon name="search" /><input placeholder="Search description or merchant" /></div>
        <select><option>All categories</option><option>Food & dining</option><option>Utilities</option></select>
        <select><option>Newest first</option><option>Highest amount</option></select>
        <input type="date" defaultValue="2026-11-01" />
        <div className="amount-range"><input placeholder="Min amount" /><span>–</span><input placeholder="Max amount" /></div>
      </Card>
      <div className="result-bar"><strong>7 transactions</strong><span>November 1–30, 2026</span></div>
      <TransactionTable all />
      <Card className="management-row"><div><Icon name="edit_note" /><span>Manage a transaction</span></div><select><option>Select transaction</option><option>Broadway Pizza · Rs. 1,450</option></select><Button variant="secondary">Edit selected</Button><Button variant="danger">Delete selected</Button></Card>
      {open && <Modal title="Add expense" onClose={() => setOpen(false)}><ExpenseForm onClose={() => setOpen(false)} /></Modal>}
    </div>
  );
}

function Budgets() {
  return (
    <div className="page-grid">
      <Card className="span-12 overall-budget">
        <div><span className="eyebrow">November 2026 overall budget</span><strong>Rs. 7,850 <small>of Rs. 46,000</small></strong><p>Rs. 38,150 remaining · 17% used</p></div>
        <div className="overall-progress"><Progress value={17} /><div><span>Rs. 0</span><span>Rs. 46,000</span></div></div>
        <Pill tone="indigo">On track</Pill>
      </Card>
      <Card className="span-8"><SectionTitle title="Category budgets" detail="Your monthly spending limits" /><BudgetList /></Card>
      <Card className="span-4 sticky-card">
        <SectionTitle title="Create or edit budget" detail="Changes apply to the selected month." />
        <div className="form-stack">
          <Field label="Month"><input type="month" defaultValue="2026-11" /></Field>
          <Field label="Category"><select><option>ALL — overall budget</option><option>Food & dining</option><option>Groceries</option><option>Transport</option></select></Field>
          <Field label="Budget amount"><div className="input-prefix"><span>Rs.</span><input defaultValue="46000" /></div></Field>
          <Button>Save budget</Button>
        </div>
        <div className="form-note"><Icon name="info" /><span>Category limits can add up to less than your overall budget, leaving room for flexible spending.</span></div>
      </Card>
    </div>
  );
}

function Gauge({ type = "forecast" }: { type?: "forecast" | "health" }) {
  const health = type === "health";
  return (
    <div className={`gauge ${health ? "gauge-health" : ""}`}>
      <svg viewBox="0 0 220 130" aria-hidden="true">
        <path d="M25 110 A85 85 0 0 1 195 110" pathLength="100" className="gauge-track" />
        <path d="M25 110 A85 85 0 0 1 195 110" pathLength="100" className="gauge-value" style={{ strokeDasharray: `${health ? 93 : 60} 100` }} />
        {!health && <line x1="170" y1="44" x2="177" y2="36" className="threshold" />}
      </svg>
      <div className="gauge-center"><strong>{health ? "93" : "Rs. 27,650"}</strong><span>{health ? "out of 100" : "projected spend"}</span>{health && <Pill tone="indigo">Grade A</Pill>}</div>
    </div>
  );
}

function Heatmap() {
  const vals = [0,0,0,0,0,0,2,1,0,3,0,2,1,0,4,0,1,2,0,3,1,0,2,0,4,1,0,5,2,3,0,0,0,0,0];
  return (
    <div className="heatmap">
      {["M","T","W","T","F","S","S"].map((d, i) => <span className="heat-label" key={`${d}${i}`}>{d}</span>)}
      {vals.map((value, i) => <div className={`heat-cell heat-${value}`} key={i}>{i > 5 && i < 31 ? i - 5 : ""}{value > 2 && <small>Rs. {value * 310}</small>}</div>)}
    </div>
  );
}

function SubscriptionTable() {
  return (
    <div className="table-shell">
      <table><thead><tr><th>Merchant</th><th>Cadence</th><th>Monthly cost</th><th>Last charge</th><th>Next due</th><th>Confidence</th><th>Status</th></tr></thead>
      <tbody>
        {[["Netflix","Monthly","Rs. 1,100","Nov 27","Dec 27","98%"],["Spotify","Monthly","Rs. 450","Nov 12","Dec 12","96%"],["StormFiber","Monthly","Rs. 2,200","Nov 25","Dec 25","99%"],["Gym Passport","Monthly","Rs. 3,600","Nov 4","Dec 4","88%"]].map((r) => <tr key={r[0]}>{r.map((c, i) => <td key={c} className={i === 2 ? "money" : ""}>{i === 0 ? <strong>{c}</strong> : c}</td>)}<td><Pill>Active</Pill></td></tr>)}
      </tbody></table>
    </div>
  );
}

function SmartInsights() {
  const [amount, setAmount] = useState("1500");
  const [checked, setChecked] = useState(false);
  const affordable = Number(amount) <= 5000;
  return (
    <div className="page-grid">
      <section className="insight-hero span-12">
        <div><span className="eyebrow">Safe to spend</span><strong>Rs. 37,200</strong><p>Comfortable · Rs. 1,283/day for 29 days</p></div>
        <div className="insight-hero-meta"><span><small>Budget left</small>Rs. 38,150</span><i /><span><small>Reserved for bills</small>Rs. 4,150</span></div>
      </section>
      <div className="kpi-grid kpi-grid-3 span-12">
        <KPI label="Budget left" value="Rs. 38,150" detail="83% of monthly limit" />
        <KPI label="Reserved for bills" value="Rs. 4,150" detail="4 upcoming recurring charges" />
        <KPI label="Daily allowance" value="Rs. 1,283" detail="For the next 29 days" />
      </div>
      <Card className="span-5">
        <SectionTitle title="Month-end forecast" detail="Based on your current spending pace" action={<Pill tone="indigo">On track</Pill>} />
        <Gauge />
        <div className="forecast-stats"><div><span>Monthly budget</span><strong>Rs. 46,000</strong></div><div><span>Run rate</span><strong>Rs. 725/day</strong></div><div><span>Time left</span><strong>29 days</strong></div></div>
      </Card>
      <Card className="span-7">
        <SectionTitle title="Financial health" detail="A weighted view of your current financial habits" />
        <div className="health-layout">
          <Gauge type="health" />
          <div className="health-components">
            {[["Budget pace","100","Spending is well below the monthly pace."],["Category control","100","No category is close to its limit."],["Recurring load","70.5","Recurring costs use 16% of budget."],["Spending stability","100","Daily variation remains controlled."],["Goal progress","80","Both goals are progressing on schedule."]].map(([name, score, copy]) => <div className="health-row" key={name}><div><strong>{name}</strong><span>{copy}</span></div><b>{score}</b></div>)}
            <div className="next-step"><Icon name="arrow_forward" /><span><strong>Next step</strong> Review recurring costs before adding another subscription.</span></div>
          </div>
        </div>
      </Card>
      <Card className="span-12">
        <SectionTitle title="Subscription hunter" detail="Recurring charges detected from your transactions" action={<Button variant="secondary">Review recurring rules</Button>} />
        <div className="mini-kpis"><div><span>Active recurring</span><strong>4</strong></div><div><span>Monthly recurring</span><strong>Rs. 7,350</strong></div><div><span>Price hikes / stale</span><strong>0 / 0</strong></div></div>
        <SubscriptionTable />
        <details className="details-row"><summary><span><Icon name="archive" /> Possibly cancelled</span><span>0 subscriptions <Icon name="expand_more" /></span></summary><p>No stale recurring charges were found.</p></details>
      </Card>
      <Card className="span-7"><SectionTitle title="Spending heatmap" detail="November 2026 · darker cells indicate higher spend" /><Heatmap /><div className="heat-legend"><span>Less</span>{[0,1,2,3,4,5].map(x => <i className={`heat-${x}`} key={x} />)}<span>More</span></div></Card>
      <Card className="span-5">
        <SectionTitle title="Monthly recap" detail="Your financial story in five points" />
        <div className="recap"><strong>You spent Rs. 4,650 in 2026-11, 93% less than the previous month.</strong><ul><li>Groceries was your top category at Rs. 2,480.</li><li>Your largest expense was Naheed Supermarket.</li><li>Four recurring charges total Rs. 7,350 monthly.</li><li>You are forecast to finish Rs. 18,350 under budget.</li><li>Both savings goals remain on track.</li></ul></div>
      </Card>
      <Card className="span-5">
        <SectionTitle title="Can I afford this?" detail="Check a purchase against your safe-to-spend amount." />
        <form className="afford-form" onSubmit={(e) => { e.preventDefault(); setChecked(true); }}><div className="input-prefix"><span>Rs.</span><input value={amount} onChange={(e) => { setAmount(e.target.value); setChecked(false); }} /></div><Button type="submit">Check purchase</Button></form>
        {checked && <div className={`verdict ${affordable ? "yes" : "no"}`}><Icon name={affordable ? "check_circle" : "warning"} /><div><strong>{affordable ? `Yes — Rs. ${Number(amount).toLocaleString()} still leaves Rs. ${(37200 - Number(amount)).toLocaleString()}.` : "Not comfortably — this would reduce your safety buffer."}</strong><span>{affordable ? "This purchase fits your current daily allowance and forecast." : "Consider delaying it or reducing the purchase amount."}</span></div></div>}
      </Card>
      <Card className="span-7 debt-card">
        <details open><summary><div><Icon name="finance" /><span><strong>Debt payoff planner</strong><small>Compare avalanche and snowball strategies</small></span></div><Icon name="expand_more" /></summary>
          <div className="debt-result"><strong>Avalanche clears the debt in 24 months with Rs. 58,575 interest.</strong><div><span><small>Avalanche</small>24 months <b>Rs. 58,575 interest</b></span><span><small>Snowball</small>24 months <b>Rs. 58,575 interest</b></span></div><p>Payoff order: HBL Credit Card → Personal Loan</p></div>
        </details>
      </Card>
    </div>
  );
}

function Goals() {
  const [modal, setModal] = useState<"new" | "add" | null>(null);
  return (
    <div className="page-stack">
      <div className="kpi-grid kpi-grid-3"><KPI label="Goals" value="2" detail="Both actively funded" /><KPI label="Saved so far" value="Rs. 125,000" detail="22.7% of Rs. 550,000" /><KPI label="Needs attention" value="0" detail="No goals are behind" /></div>
      <SectionTitle title="Your goals" detail="Track progress and keep your monthly contributions on pace." action={<Button onClick={() => setModal("new")}><Icon name="add" size="sm" /> New goal</Button>} />
      <div className="goal-grid">
        {[{name:"Emergency fund",saved:85000,target:300000,date:"2027-05-28",kind:"safety",status:"On track",monthly:"Rs. 30,715"},{name:"Northern areas trip",saved:40000,target:250000,date:"2027-09-15",kind:"travel",status:"In progress",monthly:"Rs. 21,000"}].map((g) => <Card className="goal-card" key={g.name}>
          <div className="goal-top"><div className="goal-icon"><Icon name={g.kind === "safety" ? "shield" : "flight"} /></div><Pill tone={g.status === "On track" ? "indigo" : "neutral"}>{g.status}</Pill></div>
          <h3>{g.name}</h3><div className="goal-money"><strong>Rs. {g.saved.toLocaleString()}</strong><span>of Rs. {g.target.toLocaleString()}</span></div><Progress value={g.saved/g.target*100} />
          <div className="goal-progress"><strong>{(g.saved/g.target*100).toFixed(1)}% funded</strong><span>{g.monthly}/month needed</span></div>
          <div className="goal-meta"><span>{g.kind}</span><i />Target {g.date}<i />Rs. {(g.target-g.saved).toLocaleString()} remaining</div>
          <div className="goal-actions"><Button onClick={() => setModal("add")}>Add money</Button><Button variant="ghost">Delete</Button></div>
        </Card>)}
      </div>
      <div className="caption"><Icon name="info" /><span>A goal is marked behind schedule when its current balance is below the expected balance for today based on a steady monthly contribution.</span></div>
      {modal && <Modal title={modal === "new" ? "New savings goal" : "Add contribution"} onClose={() => setModal(null)}>
        {modal === "new" ? <div className="form-stack"><Field label="Goal name"><input placeholder="e.g. Education fund" /></Field><div className="form-grid"><Field label="Target amount"><input placeholder="Rs. 0" /></Field><Field label="Already saved"><input placeholder="Rs. 0" /></Field></div><div className="form-grid"><Field label="Target date"><input type="date" /></Field><Field label="Goal type"><select><option>safety</option><option>purchase</option><option>travel</option><option>education</option><option>general</option></select></Field></div><div className="modal-actions"><Button variant="secondary" onClick={() => setModal(null)}>Cancel</Button><Button onClick={() => setModal(null)}>Create goal</Button></div></div> :
        <div className="form-stack"><p className="modal-copy">Add money to <strong>Emergency fund</strong>. This will update the saved balance immediately.</p><Field label="Contribution amount"><div className="input-prefix"><span>Rs.</span><input placeholder="0" autoFocus /></div></Field><div className="modal-actions"><Button variant="secondary" onClick={() => setModal(null)}>Cancel</Button><Button onClick={() => setModal(null)}>Add contribution</Button></div></div>}
      </Modal>}
    </div>
  );
}

function AIAssistant() {
  const [messages, setMessages] = useState([{user:false,text:"Good morning. Your November spending is comfortably on track. You have Rs. 37,200 safe to spend after upcoming bills."},{user:true,text:"What changed compared with last month?"},{user:false,text:"You’ve spent Rs. 4,650 so far—93% less than the previous month. Groceries is your largest category, while dining is the only area showing an unusual transaction."}]);
  const [input, setInput] = useState("");
  const send = (e: FormEvent) => {e.preventDefault(); if(!input.trim()) return; setMessages([...messages,{user:true,text:input},{user:false,text:"Based on your current budget, that looks manageable. I’ll keep your recurring bills and goal contributions reserved in the calculation."}]); setInput("");};
  return (
    <div className="assistant-layout">
      <aside className="session-sidebar"><Button><Icon name="add" size="sm" /> New session</Button><span className="eyebrow">Recent sessions</span><button className="session active"><strong>November spending review</strong><small>Today, 10:42</small></button><button className="session"><strong>Trip affordability</strong><small>Yesterday</small></button><button className="session"><strong>Recurring bills</strong><small>Nov 25</small></button></aside>
      <div className="chat-panel">
        <div className="connection-banner"><div><span className="status-dot" /><strong>Grok connected</strong><span>grok-4-fast · key from grok_api_key.txt</span></div><Pill tone="indigo">MCP</Pill></div>
        <div className="messages">
          <div className="chat-date">Today</div>
          {messages.map((m,i) => <div className={`message ${m.user ? "user-message" : "assistant-message"}`} key={i}>{!m.user && <div className="bot-mark"><Icon name="auto_awesome" /></div>}<div><p>{m.text}</p>{!m.user && <><span className="tool-tag"><Icon name="build" size="sm" /> Used tool: get_spending_summary</span><details className="source"><summary>2 sources <Icon name="expand_more" size="sm" /></summary><span>November transactions · Monthly budget</span></details></>}</div></div>)}
          <div className="memory-note"><Icon name="memory" size="sm" /> Used 2 long-term facts from Agent Memory</div>
        </div>
        <div className="composer"><div className="prompts"><button onClick={() => setInput("Can I afford Rs. 5,000?")}>Can I afford Rs. 5,000?</button><button onClick={() => setInput("Summarize this month")}>Summarize this month</button><button onClick={() => setInput("Find subscriptions")}>Find subscriptions</button></div><form onSubmit={send}><input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about spending, budgets, goals, or subscriptions..." /><Button type="submit" disabled={!input.trim()}><Icon name="arrow_upward" /></Button></form><span>Answers use synthetic demo data and may require verification.</span></div>
      </div>
    </div>
  );
}

function AgentMemory() {
  const [tab, setTab] = useState("Long-term facts");
  const facts = [["preferred_currency","PKR","preference","High"],["home_city","Karachi","profile","Medium"],["salary_day","1st of each month","income","High"],["risk_preference","Conservative","preference","Medium"]];
  return (
    <div className="page-stack">
      <div className="tabs">{["Long-term facts","Session transcripts","Tool audit"].map(t => <button className={tab===t?"active":""} onClick={() => setTab(t)} key={t}>{t}</button>)}</div>
      {tab === "Long-term facts" && <div className="page-grid">
        <Card className="span-8"><SectionTitle title="Stored facts" detail="Durable information used to personalize answers." /><div className="table-shell"><table><thead><tr><th>Key</th><th>Value</th><th>Category</th><th>Importance</th><th /></tr></thead><tbody>{facts.map(f=><tr key={f[0]}><td className="mono">{f[0]}</td><td><strong>{f[1]}</strong></td><td>{f[2]}</td><td><Pill tone={f[3]==="High"?"indigo":"neutral"}>{f[3]}</Pill></td><td><button className="icon-button"><Icon name="delete" size="sm" /></button></td></tr>)}</tbody></table></div></Card>
        <Card className="span-4 sticky-card"><SectionTitle title="Add fact" detail="Store a detail for future conversations." /><div className="form-stack"><Field label="Key"><input placeholder="e.g. preferred_bank" /></Field><Field label="Value"><input placeholder="Fact value" /></Field><Field label="Category"><select><option>preference</option><option>profile</option><option>income</option></select></Field><Field label="Importance"><select><option>Medium</option><option>High</option><option>Low</option></select></Field><Button>Save fact</Button></div></Card>
      </div>}
      {tab === "Session transcripts" && <Card><SectionTitle title="Session transcripts" detail="Conversation history retained for continuity." /><div className="transcript"><div><button className="active"><strong>November spending review</strong><span>6 messages · Today</span></button><button><strong>Trip affordability</strong><span>4 messages · Yesterday</span></button></div><section><span className="eyebrow">November spending review</span><p><strong>You</strong> What changed compared with last month?</p><p><strong>Assistant</strong> You’ve spent Rs. 4,650 so far—93% less than the previous month.</p></section></div></Card>}
      {tab === "Tool audit" && <Card><SectionTitle title="Tool audit" detail="A transparent log of agent tool calls." /><div className="table-shell"><table><thead><tr><th>Tool name</th><th>Transport</th><th>Timestamp</th><th>Result</th></tr></thead><tbody>{[["get_spending_summary","MCP","2026-11-30 10:42:18"],["get_budget_status","MCP","2026-11-30 10:42:19"],["search_transactions","local","2026-11-29 16:08:04"]].map(r=><tr key={r[2]}><td className="mono">{r[0]}</td><td><Pill tone={r[1]==="MCP"?"indigo":"neutral"}>{r[1]}</Pill></td><td>{r[2]}</td><td>Success</td></tr>)}</tbody></table></div></Card>}
    </div>
  );
}

function Settings() {
  const [mcp, setMcp] = useState(true);
  return (
    <div className="settings-stack">
      <Card><SectionTitle title="AI connection" detail="Manage the model and transport used by your assistant." /><div className="setting-row"><div className="setting-icon"><Icon name="key" /></div><div><strong>Grok API key</strong><span>Loaded securely from grok_api_key.txt · ending in ••••7K2</span></div><Pill tone="indigo"><span className="status-dot" /> Connected</Pill><Button variant="secondary">Test connection</Button></div><div className="setting-row"><div className="setting-icon"><Icon name="hub" /></div><div><strong>MCP transport</strong><span>Route supported assistant tools through the MCP server.</span></div><button className={`toggle ${mcp?"on":""}`} onClick={() => setMcp(!mcp)} aria-label="Toggle MCP"><span /></button></div></Card>
      <Card><SectionTitle title="Data and storage" detail="Configure local storage and semantic search." /><div className="setting-form"><Field label="Embedding backend"><select><option>Local · sentence-transformers</option><option>Disabled</option></select></Field><Field label="Database path"><input value="./data/expense_tracker.db" readOnly /></Field><Button variant="secondary">Validate path</Button></div></Card>
      <Card><SectionTitle title="Diagnostics" detail="Current capabilities and service status." /><div className="diagnostics"><div><span>Available tools</span><strong>18</strong></div><div><span>MCP status</span><strong>Connected</strong></div><div><span>Embedding index</span><strong>Ready</strong></div><div><span>Last sync</span><strong>Just now</strong></div></div></Card>
      <Card className="danger-zone"><SectionTitle title="Demo data" detail="Restore the original synthetic data set." /><div><p>This resets all transactions, budgets, goals, memories, and sessions. This action cannot be undone.</p><Button variant="danger"><Icon name="restart_alt" size="sm" /> Seed / reset demo data</Button></div></Card>
      <div className="disclaimer"><Icon name="info" /><span><strong>Synthetic demo data only.</strong> No real financial accounts are connected, and all names, transactions, and amounts shown are fictional.</span></div>
    </div>
  );
}

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
  const [page, setPage] = useState<Page>("Dashboard");
  const [drawer, setDrawer] = useState(false);
  const PageContent = useMemo(() => pages[page], [page]);
  const navigate = (next: Page) => { setPage(next); setDrawer(false); window.scrollTo({ top: 0, behavior: "smooth" }); };
  return (
    <div className="app-shell">
      <aside className={`sidebar ${drawer ? "drawer-open" : ""}`}>
        <div className="brand"><div><span className="brand-mark"><i /></span><strong>Expense Tracker</strong></div><small>AI Agent · AIDE3313</small></div>
        <div className="workspace-switcher">
          <span className="workspace-avatar">AK</span>
          <div><small>Workspace</small><strong>Personal finances</strong></div>
          <Icon name="unfold_more" size="sm" />
        </div>
        <span className="nav-label">Product</span>
        <nav>{nav.map((item) => <button className={page === item.label ? "active" : ""} onClick={() => navigate(item.label)} key={item.label}><Icon name={item.icon} /><span>{item.label}</span>{page === item.label && <i />}</button>)}</nav>
        <div className="sidebar-foot"><div className="avatar">AK</div><div><strong>Ahmed Khan</strong><span>Personal workspace</span></div><Icon name="more_horiz" /></div>
      </aside>
      {drawer && <div className="drawer-scrim" onClick={() => setDrawer(false)} />}
      <main>
        <header className="topbar">
          <button className="menu-button" onClick={() => setDrawer(true)}><Icon name="menu" /></button>
          <div><h1>{page}</h1><p>{pageCopy[page]}</p></div>
          <div className="topbar-actions">
            <button className="header-action" aria-label="Search"><Icon name="search" /></button>
            <button className="header-action notification-action" aria-label="Notifications"><Icon name="notifications" /><i /></button>
            <div className="connection"><span className="status-dot" /><span>Grok connected</span></div>
          </div>
        </header>
        <div className="content" key={page}><PageContent /></div>
      </main>
    </div>
  );
}
