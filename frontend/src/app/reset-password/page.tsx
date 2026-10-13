"use client";

import { confirmPasswordReset } from "@/lib/client-api";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="page-shell auth-page"><p>Loading reset form…</p></div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const uid = searchParams.get("uid") ?? "";
  const token = searchParams.get("token") ?? "";
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    const data = new FormData(event.currentTarget);
    try {
      await confirmPasswordReset(
        uid,
        token,
        String(data.get("new_password") ?? ""),
        String(data.get("new_password_confirm") ?? ""),
      );
      router.replace("/login?passwordReset=success");
    } catch (resetError) {
      setError(
        resetError instanceof Error
          ? resetError.message
          : "Unable to reset your password. The link may have expired.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!uid || !token) {
    return (
      <div className="page-shell auth-page">
        <div className="auth-form">
          <h1>Invalid reset link</h1>
          <p className="info-panel error-panel">
            This password reset link is incomplete. Request a new one to continue.
          </p>
          <Link className="button" href="/forgot-password">Request a new link</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell auth-page">
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        <p className="eyebrow">Account recovery</p>
        <h1>Choose a new password</h1>
        <label>
          New password
          <input autoComplete="new-password" minLength={8} name="new_password" required type="password" />
        </label>
        <label>
          Confirm new password
          <input autoComplete="new-password" minLength={8} name="new_password_confirm" required type="password" />
        </label>
        {error ? <p className="info-panel error-panel" role="alert">{error}</p> : null}
        <button className="button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Updating…" : "Reset password"}
        </button>
        <p className="muted"><Link href="/login">Back to sign in</Link></p>
      </form>
    </div>
  );
}
