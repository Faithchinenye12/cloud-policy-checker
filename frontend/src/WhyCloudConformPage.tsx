import { ArrowRight, Boxes, CheckCircle2, Database, Network, Radar, ScrollText, Server, ShieldCheck } from "lucide-react";

const journey = [
  { icon: Boxes, number: "01", title: "Resource", text: "Capture the cloud asset and the configuration evidence that describes its real security state." },
  { icon: ScrollText, number: "02", title: "Control", text: "Evaluate that evidence with deterministic, human-readable policies—not an unexplained score." },
  { icon: Network, number: "03", title: "Risk", text: "Connect failed evidence to its resource, severity, owner, and recommended remediation." },
  { icon: ShieldCheck, number: "04", title: "Readiness", text: "Map verified outcomes to recognised frameworks while remaining honest about audit scope." },
];

const architecture = [
  { icon: Server, title: "FastAPI", text: "Secure application API" },
  { icon: Database, title: "PostgreSQL", text: "Persisted evidence history" },
  { icon: Radar, title: "Celery + Redis", text: "Background scan pipeline" },
  { icon: Boxes, title: "React", text: "Focused decision workspace" },
];

export default function WhyCloudConformPage({ onExplore }: { onExplore: () => void }) {
  return <div className="why-page">
    <section className="why-hero">
      <div>
        <span className="eyebrow accent">The product story</span>
        <h1>Cloud security evidence people can actually act on.</h1>
        <p>CloudConform turns scattered configuration data into a traceable path from cloud asset to verified compliance outcome.</p>
        <button className="primary-button" onClick={onExplore}>Explore the evidence journey <ArrowRight /></button>
      </div>
      <aside>
        <span>The problem</span>
        <strong>Security dashboards often show what failed without making the evidence, ownership, and next action easy to understand.</strong>
        <p>That creates alert fatigue, slow remediation, and compliance scores that are difficult to defend.</p>
      </aside>
    </section>

    <section className="why-section">
      <header><span className="eyebrow accent">Evidence first</span><h2>One connected decision trail</h2><p>Every conclusion remains explainable from beginning to end.</p></header>
      <div className="why-journey">{journey.map(({ icon: Icon, number, title, text }, index) => <div className="why-step" key={title}><div><span>{number}</span><Icon /></div><h3>{title}</h3><p>{text}</p>{index < journey.length - 1 && <ArrowRight className="why-arrow" />}</div>)}</div>
    </section>

    <section className="why-split">
      <article className="why-principles">
        <span className="eyebrow accent">Designed to be trusted</span>
        <h2>What makes CloudConform different</h2>
        <ul>
          <li><CheckCircle2 /><div><strong>Explainable by default</strong><span>Policies state exactly what was tested, what was observed, and why it passed or failed.</span></div></li>
          <li><CheckCircle2 /><div><strong>Remediation, not noise</strong><span>Findings carry priority, ownership, action guidance, and verification history.</span></div></li>
          <li><CheckCircle2 /><div><strong>Honest assurance</strong><span>Framework views communicate evidence-based readiness without pretending to issue certification.</span></div></li>
          <li><CheckCircle2 /><div><strong>Built for clarity</strong><span>A restrained interface helps engineering, security, and leadership reach the same conclusion.</span></div></li>
        </ul>
      </article>
      <article className="why-architecture">
        <span className="eyebrow accent">Production-minded engineering</span>
        <h2>More than a dashboard</h2>
        <p>The demonstration uses the same separated application, persistence, and background-processing architecture expected of a real cloud platform.</p>
        <div>{architecture.map(({ icon: Icon, title, text }) => <section key={title}><Icon /><div><strong>{title}</strong><span>{text}</span></div></section>)}</div>
      </article>
    </section>

    <section className="why-note"><ShieldCheck /><div><strong>Built as a focused product demonstration</strong><p>The recruiter environment uses safe sample evidence. Its purpose is to demonstrate product thinking, full-stack engineering, traceability, and cloud-security workflow design.</p></div></section>
  </div>;
}
