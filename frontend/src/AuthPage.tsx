import { FormEvent, useState } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole } from "lucide-react";
import BrandMark from "./BrandMark";

export type AuthUser = {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
};

type AuthMode = "login" | "register";

export default function AuthPage({
  onAuthenticated,
}: {
  onAuthenticated: (token: string, user: AuthUser) => void;
}) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const apiBase = import.meta.env.VITE_API_URL ?? "/api";
  const publicDemo = import.meta.env.VITE_PUBLIC_DEMO === "true";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        const registerResponse = await fetch(`${apiBase}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, username, password }),
        });
        if (!registerResponse.ok) throw new Error(await readError(registerResponse));
      }

      const loginResponse = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!loginResponse.ok) throw new Error(await readError(loginResponse));

      const { access_token: token } = await loginResponse.json();
      const userResponse = await fetch(`${apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!userResponse.ok) throw new Error("Your session could not be verified.");

      onAuthenticated(token, await userResponse.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  async function exploreDemo(){setLoading(true);setError("");try{const response=await fetch(`${apiBase}/auth/demo`,{method:"POST"});if(!response.ok)throw new Error(await readError(response));const {access_token:token}=await response.json();const userResponse=await fetch(`${apiBase}/auth/me`,{headers:{Authorization:`Bearer ${token}`}});if(!userResponse.ok)throw new Error("The demo session could not be opened.");onAuthenticated(token,await userResponse.json())}catch(reason){setError(reason instanceof Error?reason.message:"The demo is unavailable.")}finally{setLoading(false)}}

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setError("");
    setPassword("");
  }

  return <main className="auth-page">
    <section className="auth-story">
      <div className="auth-brand"><span><BrandMark /></span><strong>CloudConform</strong></div>
      <div className="auth-message"><span className="eyebrow accent">Multi-cloud security platform</span><h1>Turn cloud risk into clear, actionable policy.</h1><p>Discover resources, evaluate deterministic controls, and track security posture across AWS, Azure, and Google Cloud.</p><div className="auth-proof"><span><i />Deterministic policy evaluation</span><span><i />Background scan processing</span><span><i />Secure JWT authentication</span></div></div>
      <small>Portfolio security engineering platform</small>
    </section>

    <section className="auth-form-side">
      <div className="auth-card">
        <div className="auth-mobile-brand"><BrandMark /> CloudConform</div>
        <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p>{mode === "login" ? "Sign in to view your cloud security posture." : "Set up your security workspace in a few seconds."}</p>

        {!publicDemo&&<div className="auth-tabs"><button className={mode === "login" ? "active" : ""} onClick={() => changeMode("login")}>Sign in</button><button className={mode === "register" ? "active" : ""} onClick={() => changeMode("register")}>Register</button></div>}

        <form onSubmit={submit}>
          {mode === "register" && <label>Username<input required minLength={3} maxLength={50} autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} placeholder="security-admin" /></label>}
          <label>Email address<input required type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" /></label>
          <label>Password<div className="password-field"><input required minLength={mode === "register" ? 8 : 1} maxLength={128} type={showPassword ? "text" : "password"} autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={event => setPassword(event.target.value)} placeholder={mode === "register" ? "At least 8 characters" : "Enter your password"}/><button type="button" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff /> : <Eye />}</button></div></label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" disabled={loading}>{loading ? "Please wait…" : mode === "login" ? "Sign in securely" : "Create account"}<ArrowRight /></button>
        </form>
        <div className="demo-divider"><span>or</span></div><button className="demo-entry" disabled={loading} onClick={()=>void exploreDemo()}>Explore live demo<ArrowRight/></button>
        <div className="auth-security"><LockKeyhole /><span>Your credentials are handled by the secured API and are never displayed.</span></div>
      </div>
    </section>
  </main>;
}

async function readError(response: Response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail[0]?.msg ?? "Please check your details.";
  } catch {
    return "The service returned an unexpected response.";
  }
  return "Authentication failed.";
}
