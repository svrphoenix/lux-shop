"use client";

import { requestPasswordReset } from "@/lib/client-api";
import Link from "next/link";
import { useState } from "react";

export default function ForgotPasswordPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setIsSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      const response = await requestPasswordReset(String(data.get("email") ?? ""));
      setMessage(response.detail);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to request a password reset.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-shell auth-page">
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        <p className="eyebrow">Account recovery</p>
        <h1>Forgot your password?</h1>
        <p className="muted">
          Enter the email address associated with your account. If it exists, we
          will send instructions to reset your password.
        </p>
        <label>
          Email
          <input autoComplete="email" name="email" required type="email" />
        </label>
        {message ? <p className="info-panel success-panel" role="status">{message}</p> : null}
        {error ? <p className="info-panel error-panel" role="alert">{error}</p> : null}
        <button className="button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Sending…" : "Send reset instructions"}
        </button>
        <p className="muted"><Link href="/login">Back to sign in</Link></p>
      </form>
    </div>
  );
}
