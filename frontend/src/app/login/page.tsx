"use client";

import { useAuth } from "@/components/auth-provider";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useState } from "react";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="page-shell auth-page"><p>Loading sign in…</p></div>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const passwordReset = searchParams.get("passwordReset") === "success";
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setError(null);
    try {
      await login({
        username: String(data.get("username") ?? ""),
        password: String(data.get("password") ?? ""),
      });
      router.push(searchParams.get("next") || "/account");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-shell auth-page">
      <form className="auth-form" onSubmit={(event) => void submitLogin(event)}>
        <p className="eyebrow">Welcome back</p>
        <h1>Sign in</h1>
        {passwordReset ? (
          <p className="info-panel success-panel" role="status">
            Your password has been reset. Sign in with your new password.
          </p>
        ) : null}
        <label>Username or email<input autoComplete="username" name="username" required /></label>
        <label>Password<input autoComplete="current-password" name="password" required type="password" /></label>
        {error ? <p className="info-panel error-panel">{error}</p> : null}
        <button className="button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
        <Link href="/forgot-password">Forgot your password?</Link>
        <p className="muted">New to Hop &amp; Barley? <Link href="/register">Create an account</Link>.</p>
      </form>
    </div>
  );
}
