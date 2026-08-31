import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import AuthPage, { type AuthUser } from "./AuthPage";
import {
  Activity, AlertTriangle, Bell, Boxes, CheckCircle2, ChevronDown,
  CircleUserRound, Cloud, FileBarChart, Gauge, LayoutDashboard, Menu,
  Play, Radar, ScrollText, Search, Settings, ShieldCheck, Siren, X,
} from "lucide-react";

type ApiState = "checking" | "online" | "offline";

const navigation: Array<{ label: string; icon: LucideIcon; active?: boolean }> = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Resources", icon: Boxes }, { label: "Policies", icon: ScrollText },
  { label: "Scans", icon: Radar }, { label: "Findings", icon: Siren },
  { label: "Reports", icon: FileBarChart },
];

const findings = [
  ["Critical", "Public object storage access", "prod-audit-bucket", "AWS", "CPC-S3-001"],
  ["High", "Database encryption is disabled", "payments-db", "Azure", "CPC-DB-004"],
  ["Medium", "Firewall rule allows broad ingress", "analytics-vpc", "GCP", "CPC-NET-007"],
];

const scans = [
  { name: "Production inventory", state: "Completed", time: "8 minutes ago", progress: 100 },
  { name: "Azure policy review", state: "Evaluating", time: "Started 2 minutes ago", progress: 68 },
  { name: "GCP resource discovery", state: "Queued", time: "Waiting for worker", progress: 12 },
];

export default function App() {
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [mobileNav, setMobileNav] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 5000);
    fetch(`${import.meta.env.VITE_API_URL ?? "/api"}/health`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error(); setApiState("online"); })
      .catch(() => setApiState("offline"))
      .finally(() => window.clearTimeout(timer));
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("cpc_access_token");
    if (!token) { setAuthChecked(true); return; }
    fetch(`${import.meta.env.VITE_API_URL ?? "/api"}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(setUser)
      .catch(() => localStorage.removeItem("cpc_access_token"))
      .finally(() => setAuthChecked(true));
  }, []);

  function authenticated(token: string, currentUser: AuthUser) {
    localStorage.setItem("cpc_access_token", token);
    setUser(currentUser);
    setAuthChecked(true);
  }

  function logout() {
    localStorage.removeItem("cpc_access_token");
    setUser(null);
  }

  if (!authChecked) return <main className="auth-loading"><ShieldCheck /><span>Securing your workspace…</span></main>;
  if (!user) return <AuthPage onAuthenticated={authenticated} />;

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
      <div className="brand-row"><div className="brand-icon"><ShieldCheck /></div><div><strong>Cloud Policy</strong><span>Checker</span></div><button className="icon-button mobile-close" onClick={() => setMobileNav(false)}><X /></button></div>
      <div className="workspace-card"><span className="eyebrow">Workspace</span><button><Cloud /> Production Cloud <ChevronDown /></button></div>
      <nav><span className="nav-heading">Security posture</span>{navigation.map(({ label, icon: Icon, active }) => <a className={active ? "active" : ""} href={`#${label.toLowerCase()}`} key={label}><Icon />{label}{label === "Findings" && <span className="nav-count">12</span>}</a>)}</nav>
      <div className="sidebar-footer"><a href="#settings"><Settings /> Settings</a><button className="user-card" onClick={logout} title="Sign out"><CircleUserRound /><div><strong>{user.username}</strong><span>Sign out</span></div></button></div>
    </aside>
    {mobileNav && <button className="nav-scrim" onClick={() => setMobileNav(false)} />}

    <main className="main-content">
      <header className="topbar"><button className="icon-button menu-button" onClick={() => setMobileNav(true)}><Menu /></button><div className="search-box"><Search /><input aria-label="Search" placeholder="Search resources, policies, or findings" /></div><div className="topbar-actions"><div className={`api-status ${apiState}`}><span /> API {apiState}</div><button className="icon-button"><Bell /><i /></button></div></header>
      <div className="page-content">
        <section className="page-heading"><div><span className="eyebrow accent">Unified cloud security</span><h1>Security posture overview</h1><p>Monitor policy compliance, cloud resources, and scan activity from one place.</p></div><button className="primary-button"><Play /> Run new scan</button></section>
        <div className="preview-notice"><Activity /><div><strong>Dashboard preview</strong><span>Visual metrics use demonstration data. API connectivity is live.</span></div></div>
        <section className="metrics-grid"><Metric icon={Gauge} label="Compliance score" value="84%" detail="6% improvement" tone="cyan"/><Metric icon={Boxes} label="Cloud resources" value="1,248" detail="Across 3 providers" tone="blue"/><Metric icon={AlertTriangle} label="Open findings" value="12" detail="2 critical findings" tone="orange"/><Metric icon={Radar} label="Scans this month" value="36" detail="34 completed" tone="purple"/></section>

        <section className="dashboard-grid">
          <article className="panel posture-panel"><Heading title="Security posture" subtitle="Compliance trend across all connected clouds" action="Last 30 days"/><div className="posture-body"><div className="score-ring"><div><strong>84</strong><span>out of 100</span></div></div><div className="trend-area"><div className="trend-bars">{[51,57,54,63,66,71,69,76,81,84].map((height,index) => <span key={index} style={{height:`${height}%`}}/>)}</div><div className="chart-labels"><span>Aug 1</span><span>Aug 15</span><span>Today</span></div></div></div><div className="posture-summary"><span><i className="passed"/>1,046 compliant</span><span><i className="failed"/>202 require attention</span></div></article>
          <article className="panel providers-panel"><Heading title="Cloud coverage" subtitle="Resource posture by provider"/><Provider name="Amazon Web Services" short="AWS" score={88} resources="714 resources" tone="aws"/><Provider name="Microsoft Azure" short="AZ" score={81} resources="326 resources" tone="azure"/><Provider name="Google Cloud" short="GCP" score={79} resources="208 resources" tone="gcp"/><button className="text-button">View all cloud resources →</button></article>
        </section>

        <section className="dashboard-grid lower-grid">
          <article className="panel findings-panel" id="findings"><Heading title="Priority findings" subtitle="Risks that need attention first" action="View all findings"/><div className="table-wrap"><table><thead><tr><th>Severity</th><th>Finding</th><th>Resource</th><th>Provider</th><th>Control</th></tr></thead><tbody>{findings.map(([severity,finding,resource,provider,control]) => <tr key={control}><td><span className={`severity ${severity.toLowerCase()}`}>{severity}</span></td><td><strong>{finding}</strong></td><td>{resource}</td><td>{provider}</td><td className="control-id">{control}</td></tr>)}</tbody></table></div></article>
          <article className="panel scans-panel" id="scans"><Heading title="Recent scans" subtitle="Background job activity"/><div className="pipeline"><span className="complete">Inventory</span><i/><span className="active">Queue</span><i/><span>Evaluate</span><i/><span>Results</span></div><div className="scan-list">{scans.map(scan => <div className="scan-item" key={scan.name}><div className="scan-title"><span className={`scan-icon ${scan.state.toLowerCase()}`}>{scan.state === "Completed" ? <CheckCircle2/> : <Activity/>}</span><div><strong>{scan.name}</strong><span>{scan.time}</span></div><em>{scan.state}</em></div><div className="progress-track"><span style={{width:`${scan.progress}%`}}/></div></div>)}</div></article>
        </section>
      </div>
    </main>
  </div>;
}

function Metric({icon:Icon,label,value,detail,tone}:{icon:LucideIcon;label:string;value:string;detail:string;tone:string}) { return <article className="metric-card"><div className={`metric-icon ${tone}`}><Icon/></div><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></article>; }
function Heading({title,subtitle,action}:{title:string;subtitle:string;action?:string}) { return <div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div>{action && <button>{action}{action.includes("days") && <ChevronDown/>}</button>}</div>; }
function Provider({name,short,score,resources,tone}:{name:string;short:string;score:number;resources:string;tone:string}) { return <div className="provider-row"><span className={`provider-logo ${tone}`}>{short}</span><div className="provider-info"><div><strong>{name}</strong><span>{score}%</span></div><div className="progress-track"><span style={{width:`${score}%`}}/></div><small>{resources}</small></div></div>; }
