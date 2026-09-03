import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, CircleAlert, ExternalLink, RefreshCw, ShieldCheck } from "lucide-react";

type Control={code:string;title:string;domain:string;status:"passed"|"failed"|"accepted"|"not_assessed";mapped_policies:number;evidence_count:number};
type Framework={slug:string;name:string;version:string;description:string;source_url:string;readiness_percent:number;passed:number;failed:number;accepted:number;not_assessed:number;controls:Control[]};
type Readiness={disclaimer:string;frameworks:Framework[]};

export default function CompliancePage({token}:{token:string}){
  const api=import.meta.env.VITE_API_URL??"/api";
  const [data,setData]=useState<Readiness|null>(null);const [loading,setLoading]=useState(true);const [error,setError]=useState("");
  const load=useCallback(async()=>{setLoading(true);setError("");try{const response=await fetch(`${api}/compliance/readiness`,{headers:{Authorization:`Bearer ${token}`}});if(!response.ok)throw new Error("Compliance readiness could not be loaded.");setData(await response.json());}catch(reason){setError(reason instanceof Error?reason.message:"Compliance readiness could not be loaded.");}finally{setLoading(false)}},[api,token]);
  useEffect(()=>{void load()},[load]);
  if(loading)return <div className="resource-state compliance-state"><RefreshCw className="spinning"/><strong>Connecting framework evidence…</strong></div>;
  if(error||!data)return <div className="resource-error">{error||"Compliance readiness is unavailable."}</div>;
  return <><section className="page-heading"><div><span className="eyebrow accent">Evidence-based assurance</span><h1>Compliance readiness</h1><p>Translate verified cloud configuration evidence into an honest, traceable framework view.</p></div><button className="refresh-button" onClick={()=>void load()}><RefreshCw/> Refresh evidence</button></section>
    <div className="compliance-disclaimer"><ShieldCheck/><span>{data.disclaimer}</span></div>
    <section className="framework-grid">{data.frameworks.map(framework=><article className="panel framework-card" key={framework.slug}><header><div><span className="eyebrow">{framework.version}</span><h2>{framework.name}</h2><p>{framework.description}</p></div><div className="readiness-ring" style={{"--readiness":`${framework.readiness_percent*3.6}deg`} as React.CSSProperties}><strong>{framework.readiness_percent}%</strong></div></header><div className="framework-summary"><span><b>{framework.passed}</b> Passed</span><span><b>{framework.failed}</b> Gaps</span><span><b>{framework.not_assessed}</b> Not assessed</span></div><div className="control-list">{framework.controls.map(control=><div key={control.code}><span className={`control-status ${control.status}`}>{control.status==="passed"?<CheckCircle2/>:<CircleAlert/>}</span><div><strong>{control.code} · {control.title}</strong><small>{control.domain} · {control.evidence_count} evidence result{control.evidence_count===1?"":"s"}</small></div><em className={control.status}>{control.status.replace("_"," ")}</em></div>)}</div><a href={framework.source_url} target="_blank" rel="noreferrer">Official framework source <ExternalLink/></a></article>)}</section>
  </>;
}
