"use client";

import { useAuth } from "@/components/auth-provider";
import { ApiError, removeUserAvatar, updateUserAvatar, updateUserProfile } from "@/lib/client-api";
import { getAssetUrl } from "@/lib/api";
import { useEffect, useState } from "react";

const avatarPresets = Array.from({ length: 10 }, (_, index) => `avatar${index + 1}`);

export function AccountProfileForm() {
  const { user, updateUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(user?.profile.avatar_preset ?? "");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [avatarMessage, setAvatarMessage] = useState<string | null>(null);
  const [isSavingAvatar, setIsSavingAvatar] = useState(false);
  const [avatarChanged, setAvatarChanged] = useState(false);
  const [avatarInputKey, setAvatarInputKey] = useState(0);

  useEffect(() => {
    return () => {
      if (avatarPreview) {
        URL.revokeObjectURL(avatarPreview);
      }
    };
  }, [avatarPreview]);

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

  const saveAvatar = async () => {
    setAvatarError(null);
    setAvatarMessage(null);
    setIsSavingAvatar(true);
    try {
      const data = new FormData();
      if (avatarFile) {
        data.append("avatar", avatarFile);
      } else if (selectedPreset) {
        data.append("avatar_preset", selectedPreset);
      } else {
        setAvatarError("Choose an avatar or select an image to upload.");
        return;
      }
      const updatedUser = await updateUserAvatar(data);
      updateUser(updatedUser);
      setSelectedPreset(updatedUser.profile.avatar_preset);
      setAvatarFile(null);
      setAvatarPreview(null);
      setAvatarInputKey((key) => key + 1);
      setAvatarChanged(false);
      setAvatarMessage("Your avatar has been updated.");
    } catch (saveError) {
      setAvatarError(
        saveError instanceof ApiError || saveError instanceof Error
          ? saveError.message
          : "Unable to update your avatar.",
      );
    } finally {
      setIsSavingAvatar(false);
    }
  };

  const clearAvatar = async () => {
    setAvatarError(null);
    setAvatarMessage(null);
    setIsSavingAvatar(true);
    try {
      const updatedUser = await removeUserAvatar();
      updateUser(updatedUser);
      setSelectedPreset("");
      setAvatarFile(null);
      setAvatarPreview(null);
      setAvatarInputKey((key) => key + 1);
      setAvatarChanged(false);
      setAvatarMessage("Your avatar has been removed.");
    } catch (removeError) {
      setAvatarError(
        removeError instanceof ApiError || removeError instanceof Error
          ? removeError.message
          : "Unable to remove your avatar.",
      );
    } finally {
      setIsSavingAvatar(false);
    }
  };

  const currentAvatar = avatarPreview
    ? avatarPreview
    : selectedPreset
      ? `/img/avatars/${selectedPreset}.svg`
      : user.profile.avatar
        ? getAssetUrl(user.profile.avatar)
        : null;
  const hasSavedAvatar = Boolean(user.profile.avatar || user.profile.avatar_preset);

  return (
    <section className="account-panel" aria-labelledby="profile-heading">
      <div className="account-panel-heading">
        <div>
          <p className="eyebrow">Account settings</p>
          <h2 id="profile-heading">Personal information</h2>
        </div>
      </div>
      <form className="account-profile-form" onSubmit={(event) => void saveProfile(event)}>
        <fieldset className="avatar-fields">
          <legend>Profile avatar</legend>
          <div className="account-avatar-current">
            {currentAvatar ? (
              <img className="account-avatar-preview" src={currentAvatar} alt="Avatar preview" />
            ) : (
              <span className="account-avatar-placeholder" aria-hidden="true">
                {user.username.slice(0, 1).toUpperCase()}
              </span>
            )}
            <label>
              Upload your own image
              <input
                key={avatarInputKey}
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => {
                  const file = event.currentTarget.files?.[0] ?? null;
                  setAvatarFile(file);
                  setAvatarPreview(file ? URL.createObjectURL(file) : null);
                  setSelectedPreset("");
                  setAvatarChanged(Boolean(file));
                  setAvatarError(null);
                  setAvatarMessage(null);
                }}
                type="file"
              />
              <span className="muted">JPEG, PNG, or WebP, up to 5 MB.</span>
            </label>
          </div>
          <p className="avatar-options-label">Or choose one of the existing avatars</p>
          <div className="account-avatar-options">
            {avatarPresets.map((preset) => (
              <label className="account-avatar-option" key={preset}>
                <input
                  checked={selectedPreset === preset}
                  name="avatar-preset"
                  onChange={() => {
                    setSelectedPreset(preset);
                    setAvatarFile(null);
                    setAvatarChanged(true);
                    setAvatarError(null);
                    setAvatarMessage(null);
                  }}
                  type="radio"
                  value={preset}
                />
                <img src={`/img/avatars/${preset}.svg`} alt="" />
                <span>{preset.replace("avatar", "Avatar ")}</span>
              </label>
            ))}
          </div>
          {avatarError ? <p className="info-panel error-panel">{avatarError}</p> : null}
          {avatarMessage ? <p className="info-panel success-panel">{avatarMessage}</p> : null}
          <div className="account-profile-actions">
            {hasSavedAvatar ? (
              <button
                className="button button-secondary"
                disabled={isSavingAvatar}
                onClick={() => void clearAvatar()}
                type="button"
              >
                Remove avatar
              </button>
            ) : null}
            <button
              className="button"
              disabled={isSavingAvatar || !avatarChanged}
              onClick={() => void saveAvatar()}
              type="button"
            >
              {isSavingAvatar ? "Saving avatar…" : "Save avatar"}
            </button>
          </div>
        </fieldset>
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
