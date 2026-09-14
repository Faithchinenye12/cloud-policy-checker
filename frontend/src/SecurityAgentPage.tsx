import { FormEvent, useState } from "react";
import { Bot, CheckCircle2, LockKeyhole, Send, ShieldCheck, Sparkles } from "lucide-react";

type AgentResponse = {
  answer: string;
  mode: "evidence_preview" | "strands_bedrock";
  evidence: { resources:number; policies:number; scans:number; open_findings:number; risk_score:number };
  tools_used: string[];
  disclaimer: string;
};

const suggestedQuestions = [
  "What is our highest-priority security risk?",
  "Explain the evidence behind the current risk score.",
  "What should the security team do next?",
];

export default function SecurityAgentPage({token}:{token:string}) {
  const apiBase=import.meta.env.VITE_API_URL??"/api";
  const [question,setQuestion]=useState(suggestedQuestions[0]);
  const [result,setResult]=useState<AgentResponse|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");

  async function ask(event?:FormEvent) {
    event?.preventDefault();
    if(question.trim().length<3)return;
    setLoading(true);setError("");
    try {
      const response=await fetch(`${apiBase}/security-agent/analyze`,{
        method:"POST",
        headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},
        body:JSON.stringify({question:question.trim()}),
      });
      if(!response.ok)throw new Error("The Security Agent could not analyse the evidence.");
      setResult(await response.json());
    } catch(reason) {
      setError(reason instanceof Error?reason.message:"The Security Agent is unavailable.");
    } finally { setLoading(false); }
  }

  return <div className="agent-page">
    <section className="page-heading agent-heading"><div><span className="eyebrow accent">Strands-powered investigation</span><h1>CloudConform Security Agent</h1><p>Ask questions about verified security evidence and receive a grounded, read-only recommendation.</p></div><span className="agent-safety"><LockKeyhole/> Advisory only</span></section>
    <section className="agent-layout">
      <article className="panel agent-console">
        <header><span><Bot/></span><div><strong>Security evidence analyst</strong><small>Grounded in deterministic CloudConform results</small></div><em><i/> Ready</em></header>
        <div className="agent-intro"><Sparkles/><div><strong>Investigate without surrendering control</strong><p>The agent may inspect posture, findings, and traceability evidence. It cannot change resources, findings, or cloud configuration.</p></div></div>
        <div className="agent-suggestions">{suggestedQuestions.map(item=><button type="button" key={item} onClick={()=>setQuestion(item)}>{item}</button>)}</div>
        <form onSubmit={ask}><label htmlFor="agent-question">Ask about the current security posture</label><div><textarea id="agent-question" maxLength={500} rows={3} value={question} onChange={event=>setQuestion(event.target.value)} placeholder="What should the security team investigate first?"/><button disabled={loading||question.trim().length<3}><Send/>{loading?"Analysing…":"Analyse evidence"}</button></div><small>{question.length}/500</small></form>
        {error&&<div className="resource-error agent-error">{error}</div>}
        {result&&<section className="agent-answer"><header><div><ShieldCheck/><strong>Grounded assessment</strong></div><span>{result.mode==="strands_bedrock"?"Strands + Bedrock":"Evidence preview"}</span></header><p>{result.answer}</p><footer><CheckCircle2/><span>{result.disclaimer}</span></footer></section>}
      </article>
      <aside className="panel agent-boundary"><span className="eyebrow accent">Agent boundary</span><h2>Reasoning with guardrails</h2><ol><li><b>1</b><div><strong>Inspect</strong><span>Read stored scan evidence.</span></div></li><li><b>2</b><div><strong>Reason</strong><span>Use Strands with Amazon Bedrock.</span></div></li><li><b>3</b><div><strong>Recommend</strong><span>Explain the safest next action.</span></div></li></ol><div><LockKeyhole/><p><strong>No autonomous changes</strong><br/>Deterministic controls remain the source of truth.</p></div>{result&&<dl><div><dt>Risk score</dt><dd>{result.evidence.risk_score}/100</dd></div><div><dt>Open findings</dt><dd>{result.evidence.open_findings}</dd></div><div><dt>Evidence scans</dt><dd>{result.evidence.scans}</dd></div></dl>}</aside>
    </section>
  </div>;
}
