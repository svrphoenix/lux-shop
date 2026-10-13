"use client";

import { useAuth } from "@/components/auth-provider";
import { ApiError, changePassword } from "@/lib/client-api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function ChangePasswordPage() {
  const { isReady, user } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isReady && !user) {
      router.replace("/login?next=/account/password");
    }
  }, [isReady, router, user]);

  const submitPasswordChange = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const newPassword = String(data.get("new_password") ?? "");
    const confirmation = String(data.get("new_password_confirm") ?? "");
    if (newPassword !== confirmation) {
      setError("The new passwords do not match.");
      setMessage(null);
      return;
    }

    setError(null);
    setMessage(null);
    setIsSubmitting(true);
    try {
      const response = await changePassword({
        old_password: String(data.get("old_password") ?? ""),
        new_password: newPassword,
        new_password_confirm: confirmation,
      });
      form.reset();
      setMessage(response.detail || "Your password has been changed.");
    } catch (changeError) {
      setError(
        changeError instanceof ApiError || changeError instanceof Error
          ? changeError.message
          : "Unable to change your password.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady || !user) {
    return <div className="page-shell simple-page"><p>Loading your account…</p></div>;
  }

  return (
    <div className="page-shell account-settings-page">
      <Link className="account-back-link" href="/account">← Back to account</Link>
      <section className="account-panel password-panel">
        <div>
          <p className="eyebrow">Security</p>
          <h1>Change password</h1>
          <p className="muted">Choose a new password for your account.</p>
        </div>
        <form
          className="account-profile-form"
          onSubmit={(event) => void submitPasswordChange(event)}
        >
          <label>
            Current password
            <input
              autoComplete="current-password"
              name="old_password"
              required
              type="password"
            />
          </label>
          <label>
            New password
            <input
              autoComplete="new-password"
              minLength={8}
              name="new_password"
              required
              type="password"
            />
          </label>
          <label>
            Confirm new password
            <input
              autoComplete="new-password"
              minLength={8}
              name="new_password_confirm"
              required
              type="password"
            />
          </label>
          {error ? <p className="info-panel error-panel">{error}</p> : null}
          {message ? <p className="info-panel success-panel">{message}</p> : null}
          <button className="button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Updating…" : "Update password"}
          </button>
        </form>
      </section>
    </div>
  );
}
