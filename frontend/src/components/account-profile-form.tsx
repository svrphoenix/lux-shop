"use client";

import { useAuth } from "@/components/auth-provider";
import { ApiError, updateUserProfile } from "@/lib/client-api";
import { useState } from "react";

export function AccountProfileForm() {
  const { user, updateUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  if (!user) {
    return null;
  }

  const saveProfile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSaving(true);
    try {
      const updatedUser = await updateUserProfile(new FormData(event.currentTarget));
      updateUser(updatedUser);
      setMessage("Your account information has been saved.");
    } catch (saveError) {
      setError(
        saveError instanceof ApiError || saveError instanceof Error
          ? saveError.message
          : "Unable to save your account information.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="account-panel" aria-labelledby="profile-heading">
      <div className="account-panel-heading">
        <div>
          <p className="eyebrow">Account settings</p>
          <h2 id="profile-heading">Personal information</h2>
        </div>
      </div>
      <form className="account-profile-form" onSubmit={(event) => void saveProfile(event)}>
        <label>
          Username
          <input autoComplete="username" disabled value={user.username} />
        </label>
        <div className="account-profile-name-fields">
          <label>
            First name
            <input
              autoComplete="given-name"
              defaultValue={user.first_name}
              name="first_name"
              required
            />
          </label>
          <label>
            Last name
            <input
              autoComplete="family-name"
              defaultValue={user.last_name}
              name="last_name"
              required
            />
          </label>
        </div>
        <label>
          Email
          <input
            autoComplete="email"
            defaultValue={user.email}
            name="email"
            required
            type="email"
          />
        </label>
        <label>
          Phone number
          <input
            autoComplete="tel"
            defaultValue={user.profile.phone_number}
            name="phone_number"
            type="tel"
          />
        </label>
        <label>
          Delivery address
          <textarea
            autoComplete="street-address"
            defaultValue={user.profile.address}
            name="address"
            rows={3}
          />
        </label>
        <label>
          Date of birth
          <input
            defaultValue={user.profile.birth_day ?? ""}
            name="birth_day"
            type="date"
          />
        </label>
        {error ? <p className="info-panel error-panel">{error}</p> : null}
        {message ? <p className="info-panel success-panel">{message}</p> : null}
        <div className="account-profile-actions">
          <button className="button" disabled={isSaving} type="submit">
            {isSaving ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>
    </section>
  );
}
