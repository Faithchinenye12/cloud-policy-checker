import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import AuthPage, { type AuthUser } from "./AuthPage";
import ResourcesPage from "./ResourcesPage";
import PoliciesPage from "./PoliciesPage";
import ScansPage from "./ScansPage";
import ReportsPage from "./ReportsPage";
import BrandMark from "./BrandMark";
import IntelligencePage from "./IntelligencePage";
import CompliancePage from "./CompliancePage";
import WhyCloudConformPage from "./WhyCloudConformPage";
import {
  Activity, AlertTriangle, Bell, Boxes, CheckCircle2, ChevronDown,
  CircleUserRound, Cloud, FileBarChart, Gauge, LayoutDashboard, Menu, Network,
  ArrowLeft, ArrowRight, Eye, HelpCircle, Play, Radar, ScrollText, Search, Settings, ShieldCheck, Siren, X,
} from "lucide-react";

type ApiState = "checking" | "online" | "waking";

const tour = [
  { view: "Resources", eyebrow: "1 · Cloud inventory", title: "Start with the asset", body: "See the cloud resource and configuration evidence that every later decision traces back to." },
  { view: "Policies", eyebrow: "2 · Deterministic controls", title: "Understand the rule", body: "Review human-readable controls and the exact configuration each policy expects." },
  { view: "Intelligence", eyebrow: "3 · Connected risk", title: "Prioritise what matters", body: "Follow stored evidence from resource to policy to finding, then see the recommended action." },
  { view: "Compliance", eyebrow: "4 · Evidence-based assurance", title: "Measure readiness honestly", body: "Translate verified results into framework readiness without claiming an audit or certification." },
];

const navigation: Array<{ label: string; icon: LucideIcon; active?: boolean }> = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Resources", icon: Boxes }, { label: "Policies", icon: ScrollText },
  { label: "Scans", icon: Radar }, { label: "Findings", icon: Siren },
  { label: "Intelligence", icon: Network },
  { label: "Compliance", icon: ShieldCheck },
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
  const publicDemo = import.meta.env.VITE_PUBLIC_DEMO === "true";
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [mobileNav, setMobileNav] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [activeView, setActiveView] = useState("Overview");
  const [tourStep, setTourStep] = useState(0);
  const [showTour, setShowTour] = useState(() => publicDemo && localStorage.getItem("cloudconform_tour_seen") !== "true");

  useEffect(() => {
    if (showTour) setActiveView(tour[tourStep].view);
  }, [showTour, tourStep]);

  useEffect(() => {
    let disposed = false;
    let retryTimer = 0;
    let controller: AbortController | null = null;
    const checkApi = () => {
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 8000);
      fetch(`${import.meta.env.VITE_API_URL ?? "/api"}/health`, { signal: controller.signal })
        .then((response) => { if (!response.ok) throw new Error(); if (!disposed) setApiState("online"); })
        .catch(() => {
          if (disposed) return;
          setApiState("waking");
          retryTimer = window.setTimeout(checkApi, 8000);
        })
        .finally(() => window.clearTimeout(timeout));
    };
    checkApi();
    return () => { disposed = true; controller?.abort(); window.clearTimeout(retryTimer); };
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

  function openTour() {
    setTourStep(0);
    setActiveView(tour[0].view);
    setShowTour(true);
  }

  function closeTour() {
    localStorage.setItem("cloudconform_tour_seen", "true");
    setShowTour(false);
  }

  function moveTour(nextStep: number) {
    if (nextStep >= tour.length) { closeTour(); return; }
    setTourStep(nextStep);
    setActiveView(tour[nextStep].view);
  }

  if (!authChecked) return <main className="auth-loading"><BrandMark /><span>Securing your workspace…</span></main>;
  if (!user) return <AuthPage onAuthenticated={authenticated} />;

  return <div className={`app-shell ${publicDemo?"public-demo":""}`}>
    <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
      <div className="brand-row"><div className="brand-icon"><BrandMark /></div><div><strong>CloudConform</strong><span>Security</span></div><button className="icon-button mobile-close" onClick={() => setMobileNav(false)}><X /></button></div>
      <div className="workspace-card"><span className="eyebrow">Workspace</span><button><Cloud /> Production Cloud <ChevronDown /></button></div>
      <nav><span className="nav-heading">Security posture</span>{[...navigation, ...(publicDemo ? [{ label: "Why CloudConform", icon: HelpCircle }] : [])].map(({ label, icon: Icon }) => <button className={activeView === label ? "active" : ""} onClick={() => { setActiveView(label); setMobileNav(false); }} key={label}><Icon />{label}</button>)}</nav>
      <div className="sidebar-footer"><a href="#settings"><Settings /> Settings</a><button className="user-card" onClick={logout} title="Sign out"><CircleUserRound /><div><strong>{user.username}</strong><span>Sign out</span></div></button></div>
    </aside>
    {mobileNav && <button className="nav-scrim" onClick={() => setMobileNav(false)} />}

    <main className="main-content">
      <header className="topbar"><button className="icon-button menu-button" onClick={() => setMobileNav(true)}><Menu /></button><div className="search-box"><Search /><input aria-label="Search" placeholder="Search resources, policies, or findings" /></div><div className="topbar-actions"><div className={`api-status ${apiState}`} title={apiState === "online" ? "CloudConform API is ready" : "The demo service is starting and will reconnect automatically"}><span /> {apiState === "online" ? "API Online" : apiState === "checking" ? "Connecting…" : "Service waking up…"}</div><button className="icon-button"><Bell /><i /></button></div></header>
      <div className="page-content">{publicDemo&&<section className="demo-banner"><div><Eye/><span><strong>Read-only recruiter demo</strong> Explore verified sample evidence without changing the shared workspace.</span><button className="tour-launch" onClick={openTour}><HelpCircle/> Guided tour</button></div><nav aria-label="Suggested demo journey"><button onClick={()=>setActiveView("Resources")}>1. Resource</button><ArrowRight/><button onClick={()=>setActiveView("Policies")}>2. Controls</button><ArrowRight/><button onClick={()=>setActiveView("Intelligence")}>3. Risk</button><ArrowRight/><button onClick={()=>setActiveView("Compliance")}>4. Readiness</button></nav></section>}{activeView === "Why CloudConform" ? <WhyCloudConformPage onExplore={openTour} /> : activeView === "Resources" ? <ResourcesPage token={localStorage.getItem("cpc_access_token") ?? ""} readOnly={publicDemo} /> : activeView === "Policies" ? <PoliciesPage token={localStorage.getItem("cpc_access_token") ?? ""} readOnly={publicDemo} /> : activeView === "Scans" || activeView === "Findings" ? <ScansPage token={localStorage.getItem("cpc_access_token") ?? ""} currentUserId={user.id} initialTab={activeView === "Findings" ? "findings" : "scans"} readOnly={publicDemo} /> : activeView === "Intelligence" ? <IntelligencePage token={localStorage.getItem("cpc_access_token") ?? ""} /> : activeView === "Compliance" ? <CompliancePage token={localStorage.getItem("cpc_access_token") ?? ""} onManageFindings={()=>setActiveView("Findings")} /> : activeView === "Reports" ? <ReportsPage token={localStorage.getItem("cpc_access_token") ?? ""} /> : <>
        <section className="page-heading"><div><span className="eyebrow accent">Unified cloud security</span><h1>Security posture overview</h1><p>Monitor policy compliance, cloud resources, and scan activity from one place.</p></div>{!publicDemo&&<button className="primary-button"><Play /> Run new scan</button>}</section>
        <div className="preview-notice"><Activity /><div><strong>Dashboard preview</strong><span>Visual metrics use demonstration data. API connectivity is live.</span></div></div>
        <section className="metrics-grid"><Metric icon={Gauge} label="Compliance score" value="84%" detail="6% improvement" tone="cyan"/><Metric icon={Boxes} label="Cloud resources" value="1,248" detail="Across 3 providers" tone="blue"/><Metric icon={AlertTriangle} label="Open findings" value="12" detail="2 critical findings" tone="orange"/><Metric icon={Radar} label="Scans this month" value="36" detail="34 completed" tone="purple"/></section>

        <section className="dashboard-grid">
          <article className="panel posture-panel"><Heading title="Security posture" subtitle="Compliance trend across all connected clouds" action="Last 30 days"/><div className="posture-body"><div className="score-ring"><div><strong>84</strong><span>out of 100</span></div></div><div className="trend-area"><div className="trend-bars">{[51,57,54,63,66,71,69,76,81,84].map((height,index) => <span key={index} style={{height:`${height}%`}}/>)}</div><div className="chart-labels"><span>Aug 1</span><span>Aug 15</span><span>Today</span></div></div></div><div className="posture-summary"><span><i className="passed"/>1,046 compliant</span><span><i className="failed"/>202 require attention</span></div></article>
          <article className="panel providers-panel"><Heading title="Cloud coverage" subtitle="Resource posture by provider"/><Provider name="Amazon Web Services" short="AWS" score={88} resources="714 resources" tone="aws"/><Provider name="Microsoft Azure" short="AZ" score={81} resources="326 resources" tone="azure"/><Provider name="Google Cloud" short="GCP" score={79} resources="208 resources" tone="gcp"/><button className="text-button">View all cloud resources →</button></article>
        </section>

        <section className="dashboard-grid lower-grid">
          <article className="panel findings-panel" id="findings"><Heading title="Priority findings" subtitle="Risks that need attention first" action="View all findings"/><div className="table-wrap"><table><thead><tr><th>Severity</th><th>Finding</th><th>Resource</th><th>Provider</th><th>Control</th></tr></thead><tbody>{findings.map(([severity,finding,resource,provider,control]) => <tr key={control}><td><span className={`severity ${severity.toLowerCase()}`}>{severity}</span></td><td><strong>{finding}</strong></td><td>{resource}</td><td>{provider}</td><td className="control-id">{control}</td></tr>)}</tbody></table></div></article>
          <article className="panel scans-panel" id="scans"><Heading title="Recent scans" subtitle="Background job activity"/><div className="pipeline"><span className="complete">Inventory</span><i/><span className="active">Queue</span><i/><span>Evaluate</span><i/><span>Results</span></div><div className="scan-list">{scans.map(scan => <div className="scan-item" key={scan.name}><div className="scan-title"><span className={`scan-icon ${scan.state.toLowerCase()}`}>{scan.state === "Completed" ? <CheckCircle2/> : <Activity/>}</span><div><strong>{scan.name}</strong><span>{scan.time}</span></div><em>{scan.state}</em></div><div className="progress-track"><span style={{width:`${scan.progress}%`}}/></div></div>)}</div></article>
        </section></>}
      </div>
    </main>
    {showTour && <div className="tour-backdrop" role="presentation"><section className="tour-card" role="dialog" aria-modal="true" aria-labelledby="tour-title"><button className="tour-close" onClick={closeTour} aria-label="Close guided tour"><X/></button><span className="eyebrow accent">{tour[tourStep].eyebrow}</span><h2 id="tour-title">{tour[tourStep].title}</h2><p>{tour[tourStep].body}</p><div className="tour-progress" aria-label={`Step ${tourStep + 1} of ${tour.length}`}>{tour.map((step,index)=><span className={index === tourStep ? "active" : index < tourStep ? "complete" : ""} key={step.view}/>)}</div><footer><small>Step {tourStep + 1} of {tour.length}</small><div>{tourStep > 0 && <button className="tour-secondary" onClick={()=>moveTour(tourStep-1)}><ArrowLeft/> Back</button>}<button className="tour-primary" onClick={()=>moveTour(tourStep+1)}>{tourStep === tour.length-1 ? "Finish tour" : "Next"}<ArrowRight/></button></div></footer></section></div>}
  </div>;
}

function Metric({icon:Icon,label,value,detail,tone}:{icon:LucideIcon;label:string;value:string;detail:string;tone:string}) { return <article className="metric-card"><div className={`metric-icon ${tone}`}><Icon/></div><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></article>; }
function Heading({title,subtitle,action}:{title:string;subtitle:string;action?:string}) { return <div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div>{action && <button>{action}{action.includes("days") && <ChevronDown/>}</button>}</div>; }
function Provider({name,short,score,resources,tone}:{name:string;short:string;score:number;resources:string;tone:string}) { return <div className="provider-row"><span className={`provider-logo ${tone}`}>{short}</span><div className="provider-info"><div><strong>{name}</strong><span>{score}%</span></div><div className="progress-track"><span style={{width:`${score}%`}}/></div><small>{resources}</small></div></div>; }
