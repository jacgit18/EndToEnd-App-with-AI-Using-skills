import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { ApiError, api } from "./api/client";

// Maps the backend's status codes to what the owner should read. The 401 text
// is deliberately the same for a wrong email and a wrong password — the API
// doesn't say which was wrong (ADR-0010), and neither should the UI.
function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "Invalid email or password.";
    if (error.status === 429) return "Too many attempts. Wait a few minutes and try again.";
  }
  return "Couldn't sign in. Check your connection and try again.";
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // api.login stores the CSRF token the response body carries (client.ts) and
  // the browser stores the HttpOnly session cookie by itself — this component
  // never touches either. Success just means "go to the app".
  const login = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: () => navigate("/", { replace: true }),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    login.mutate();
  }

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem", maxWidth: "22rem" }}>
      <h1>Sign in</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <label style={{ display: "grid", gap: "0.25rem" }}>
          Email
          <input
            type="email"
            required
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label style={{ display: "grid", gap: "0.25rem" }}>
          Password
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button type="submit" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Sign in"}
        </button>
        {login.isError && (
          <p role="alert" style={{ color: "crimson", margin: 0 }}>
            {errorMessage(login.error)}
          </p>
        )}
      </form>
    </main>
  );
}
