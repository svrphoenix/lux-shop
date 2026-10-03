"use client";

import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitRegistration = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setError(null);
    try {
      await register({
        username: String(data.get("username") ?? ""),
        email: String(data.get("email") ?? ""),
        first_name: String(data.get("first_name") ?? ""),
        last_name: String(data.get("last_name") ?? ""),
        password: String(data.get("password") ?? ""),
        password_confirm: String(data.get("password_confirm") ?? ""),
      });
      router.push("/account");
    } catch (registrationError) {
      setError(
        registrationError instanceof Error
          ? registrationError.message
          : "Unable to create account.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-shell auth-page">
      <form className="auth-form" onSubmit={(event) => void submitRegistration(event)}>
        <p className="eyebrow">Start brewing</p>
        <h1>Create an account</h1>
        <div className="form-grid">
          <label>First name<input name="first_name" required /></label>
          <label>Last name<input name="last_name" required /></label>
        </div>
        <label>Username<input autoComplete="username" name="username" required /></label>
        <label>Email<input autoComplete="email" name="email" required type="email" /></label>
        <label>Password<input autoComplete="new-password" name="password" required type="password" /></label>
        <label>Confirm password<input autoComplete="new-password" name="password_confirm" required type="password" /></label>
        {error ? <p className="info-panel error-panel">{error}</p> : null}
        <button className="button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
        <p className="muted">Already registered? <Link href="/login">Sign in</Link>.</p>
      </form>
    </div>
  );
}
