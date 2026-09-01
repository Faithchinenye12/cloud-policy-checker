import { FormEvent, useCallback, useEffect, useState } from "react";
import { Boxes, Cloud, Filter, MapPin, Plus, RefreshCw, Server, X } from "lucide-react";

type Provider = "aws" | "azure" | "gcp";
type Resource = {
  id: number;
  name: string;
  resource_type: string;
  cloud_provider: Provider;
  cloud_id: string;
  region: string | null;
  status: "active" | "inactive";
  configuration: Record<string, unknown>;
  last_discovered_at: string;
};

const emptyForm = { name: "", resource_type: "", cloud_provider: "aws" as Provider, cloud_id: "", region: "", configuration: "{}" };

export default function ResourcesPage({ token }: { token: string }) {
  const [resources, setResources] = useState<Resource[]>([]);
  const [provider, setProvider] = useState<"all" | Provider>("all");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const apiBase = import.meta.env.VITE_API_URL ?? "/api";

  const loadResources = useCallback(async () => {
    setLoading(true); setError("");
    const query = new URLSearchParams();
    if (provider !== "all") query.set("cloud_provider", provider);
    if (includeInactive) query.set("include_inactive", "true");
    try {
      const response = await fetch(`${apiBase}/resources?${query}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(await readError(response));
      setResources(await response.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Resources could not be loaded.");
    } finally { setLoading(false); }
  }, [apiBase, includeInactive, provider, token]);

  useEffect(() => { void loadResources(); }, [loadResources]);

  async function createResource(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError("");
    try {
      let configuration: Record<string, unknown>;
      try { configuration = JSON.parse(form.configuration); }
      catch { throw new Error("Configuration must be valid JSON."); }
      const response = await fetch(`${apiBase}/resources`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, region: form.region || null, configuration }),
      });
      if (!response.ok) throw new Error(await readError(response));
      setForm(emptyForm); setShowCreate(false); await loadResources();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Resource could not be created."); }
    finally { setSaving(false); }
  }

  return <>
    <section className="page-heading resources-heading"><div><span className="eyebrow accent">Cloud inventory</span><h1>Resources</h1><p>Review the cloud assets available for policy evaluation.</p></div><button className="primary-button" onClick={() => setShowCreate(true)}><Plus /> Add resource</button></section>
    <section className="resource-summary">
      <div><span><Boxes /></span><strong>{resources.length}</strong><small>Visible resources</small></div>
      {(["aws", "azure", "gcp"] as Provider[]).map(item => <div key={item}><span className={item}><Cloud /></span><strong>{resources.filter(resource => resource.cloud_provider === item).length}</strong><small>{providerName(item)}</small></div>)}
    </section>
    <section className="panel resource-panel">
      <div className="resource-toolbar"><div className="provider-filters"><Filter />{(["all", "aws", "azure", "gcp"] as const).map(item => <button className={provider === item ? "active" : ""} onClick={() => setProvider(item)} key={item}>{item === "all" ? "All providers" : item.toUpperCase()}</button>)}</div><label className="inactive-toggle"><input type="checkbox" checked={includeInactive} onChange={event => setIncludeInactive(event.target.checked)} /> Include inactive</label><button className="refresh-button" onClick={() => void loadResources()}><RefreshCw /> Refresh</button></div>
      {error && <div className="resource-error">{error}</div>}
      {loading ? <div className="resource-state"><RefreshCw className="spinning" /><strong>Loading inventory…</strong></div> : resources.length === 0 ? <div className="resource-state"><Boxes /><strong>No resources found</strong><p>Add the first cloud resource or change the selected filters.</p><button className="text-button" onClick={() => setShowCreate(true)}>Add a resource →</button></div> : <div className="resource-table-wrap"><table className="resource-table"><thead><tr><th>Resource</th><th>Provider</th><th>Type</th><th>Region</th><th>Status</th><th>Last discovered</th></tr></thead><tbody>{resources.map(resource => <tr key={resource.id}><td><div className="resource-name"><span><Server /></span><div><strong>{resource.name}</strong><small>{resource.cloud_id}</small></div></div></td><td><span className={`provider-pill ${resource.cloud_provider}`}>{resource.cloud_provider.toUpperCase()}</span></td><td>{resource.resource_type}</td><td><span className="region"><MapPin />{resource.region ?? "Global"}</span></td><td><span className={`status-pill ${resource.status}`}>{resource.status}</span></td><td>{new Date(resource.last_discovered_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
    </section>

    {showCreate && <div className="modal-backdrop" role="presentation"><section className="resource-modal" role="dialog" aria-modal="true" aria-labelledby="create-resource-title"><div className="modal-heading"><div><span className="eyebrow accent">Inventory record</span><h2 id="create-resource-title">Add cloud resource</h2><p>Create a resource that can be evaluated by policies and scans.</p></div><button className="icon-button" onClick={() => setShowCreate(false)}><X /></button></div><form onSubmit={createResource}>
      <div className="form-grid"><label>Resource name<input required maxLength={200} value={form.name} onChange={event => setForm({...form,name:event.target.value})} placeholder="Production audit bucket" /></label><label>Resource type<input required minLength={3} maxLength={100} value={form.resource_type} onChange={event => setForm({...form,resource_type:event.target.value})} placeholder="s3_bucket" /></label><label>Cloud provider<select value={form.cloud_provider} onChange={event => setForm({...form,cloud_provider:event.target.value as Provider})}><option value="aws">AWS</option><option value="azure">Azure</option><option value="gcp">Google Cloud</option></select></label><label>Region<input maxLength={100} value={form.region} onChange={event => setForm({...form,region:event.target.value})} placeholder="eu-west-2" /></label></div>
      <label>Cloud resource ID<input required maxLength={500} value={form.cloud_id} onChange={event => setForm({...form,cloud_id:event.target.value})} placeholder="arn:aws:s3:::production-audit" /></label><label>Configuration JSON<textarea required rows={6} value={form.configuration} onChange={event => setForm({...form,configuration:event.target.value})} spellCheck={false} /></label>{error&&<div className="resource-error modal-error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" onClick={() => setShowCreate(false)}>Cancel</button><button className="primary-button" disabled={saving}>{saving ? "Saving…" : "Add resource"}</button></div>
    </form></section></div>}
  </>;
}

function providerName(provider: Provider) { return provider === "aws" ? "AWS" : provider === "azure" ? "Azure" : "Google Cloud"; }
async function readError(response: Response) { try { const body = await response.json(); return typeof body.detail === "string" ? body.detail : "Please check the resource details."; } catch { return "The service returned an unexpected response."; } }
