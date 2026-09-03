import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, Boxes, Network, RefreshCw, ScanSearch, ScrollText, Target } from "lucide-react";

type NodeKind = "resource" | "policy" | "scan" | "finding";
type GraphNode = { id:string;kind:NodeKind;label:string;status:string;severity:string|null;metadata:Record<string,unknown> };
type GraphEdge = { source:string;target:string;relationship:string };
type Action = { finding_id:number;resource_id:number;policy_id:number;severity:string;title:string;recommendation:string };
type Graph = { summary:{resources:number;policies:number;scans:number;open_findings:number;risk_score:number};nodes:GraphNode[];edges:GraphEdge[];priority_actions:Action[] };

export default function IntelligencePage({token}:{token:string}) {
  const apiBase=import.meta.env.VITE_API_URL??"/api";
  const [graph,setGraph]=useState<Graph|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const load=useCallback(async()=>{setLoading(true);setError("");try{const response=await fetch(`${apiBase}/intelligence/graph`,{headers:{Authorization:`Bearer ${token}`}});if(!response.ok)throw new Error("Risk intelligence could not be loaded.");setGraph(await response.json());}catch(reason){setError(reason instanceof Error?reason.message:"Risk intelligence could not be loaded.");}finally{setLoading(false);}},[apiBase,token]);
  useEffect(()=>{void load();},[load]);
  const nodeMap=useMemo(()=>new Map(graph?.nodes.map(node=>[node.id,node])??[]),[graph]);

  if(loading)return <div className="resource-state intelligence-state"><RefreshCw className="spinning"/><strong>Connecting security evidence…</strong><p>Tracing resources, controls, scans, and findings.</p></div>;
  if(error||!graph)return <div className="resource-error intelligence-error">{error||"Risk intelligence is unavailable."}<button onClick={()=>void load()}>Try again</button></div>;
  const riskLabel=graph.summary.risk_score>=75?"Severe":graph.summary.risk_score>=40?"Elevated":graph.summary.risk_score>0?"Guarded":"Clear";

  return <>
    <section className="page-heading intelligence-heading"><div><span className="eyebrow accent">Connected security evidence</span><h1>Risk intelligence</h1><p>See how cloud assets, controls, scans, and findings connect—and what to fix first.</p></div><button className="refresh-button" onClick={()=>void load()}><RefreshCw/> Refresh evidence</button></section>
    <section className="intelligence-hero">
      <div className="risk-score"><div className={`risk-orbit risk-${riskLabel.toLowerCase()}`} style={{"--risk":`${graph.summary.risk_score*3.6}deg`} as React.CSSProperties}><span><strong>{graph.summary.risk_score}</strong><small>out of 100</small></span></div><div><span className="eyebrow">Current exposure</span><h2>{riskLabel} risk</h2><p>Calculated from stored, non-compliant evidence and weighted by policy severity.</p></div></div>
      <div className="intelligence-summary"><Summary icon={Boxes} value={graph.summary.resources} label="Connected resources"/><Summary icon={ScrollText} value={graph.summary.policies} label="Evaluated controls"/><Summary icon={ScanSearch} value={graph.summary.scans} label="Evidence scans"/><Summary icon={AlertTriangle} value={graph.summary.open_findings} label="Open findings" danger/></div>
    </section>
    <section className="intelligence-layout">
      <article className="panel evidence-map"><header><div><span className="eyebrow accent">Traceability map</span><h2>From cloud asset to action</h2><p>Every connection below comes from persisted scan evidence.</p></div><Network/></header>
        {graph.priority_actions.length===0?<Empty/>:<div className="evidence-paths">{graph.priority_actions.map(action=><EvidencePath key={action.finding_id} action={action} nodeMap={nodeMap}/>)}</div>}
      </article>
      <article className="panel action-queue"><header><div><span className="eyebrow accent">Priority queue</span><h2>Recommended next actions</h2><p>Ordered by policy severity and evidence.</p></div><Target/></header>
        {graph.priority_actions.length===0?<Empty/>:<div className="action-list">{graph.priority_actions.map((action,index)=><div className="action-item" key={action.finding_id}><span>{String(index+1).padStart(2,"0")}</span><div><div><strong>{action.title}</strong><em className={`severity ${action.severity}`}>{action.severity}</em></div><p>{action.recommendation}</p><small>Finding #{action.finding_id} · Policy #{action.policy_id}</small></div></div>)}</div>}
      </article>
    </section>
  </>;
}

function Summary({icon:Icon,value,label,danger=false}:{icon:typeof Boxes;value:number;label:string;danger?:boolean}){return <div className={danger?"danger":""}><Icon/><strong>{value}</strong><span>{label}</span></div>}
function EvidencePath({action,nodeMap}:{action:Action;nodeMap:Map<string,GraphNode>}){const resource=nodeMap.get(`resource:${action.resource_id}`);const policy=nodeMap.get(`policy:${action.policy_id}`);const finding=nodeMap.get(`finding:${action.finding_id}`);return <div className="evidence-path"><PathNode kind="Resource" label={resource?.label??`Resource #${action.resource_id}`} meta={String(resource?.metadata.provider??"").toUpperCase()} icon={Boxes}/><ArrowRight/><PathNode kind="Policy" label={policy?.label??`Policy #${action.policy_id}`} meta={action.severity} icon={ScrollText}/><ArrowRight/><PathNode kind="Finding" label={finding?.label??`Finding #${action.finding_id}`} meta="Action required" icon={AlertTriangle} danger/></div>}
function PathNode({kind,label,meta,icon:Icon,danger=false}:{kind:string;label:string;meta:string;icon:typeof Boxes;danger?:boolean}){return <div className={`path-node ${danger?"danger":""}`}><Icon/><span>{kind}</span><strong>{label}</strong><small>{meta}</small></div>}
function Empty(){return <div className="intelligence-empty"><Target/><strong>No priority actions</strong><p>Stored scan evidence currently contains no policy failures.</p></div>}
