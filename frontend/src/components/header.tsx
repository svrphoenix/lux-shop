"use client";

import { useAuth } from "@/components/auth-provider";
import { useCart } from "@/components/cart-provider";
import { getAssetUrl } from "@/lib/api";
import Link from "next/link";
import { useState } from "react";

export function Header() {
  const { isReady, logout, user } = useAuth();
  const { cart } = useCart();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const avatarUrl = user
    ? user.profile.avatar
      ? getAssetUrl(user.profile.avatar)
      : user.profile.avatar_preset
        ? `/img/avatars/${user.profile.avatar_preset}.svg`
        : null
    : null;

  return (
    <header className="site-header">
      <div className="page-shell header-inner">
        <Link className="brand" href="/" aria-label="Hop & Barley home">
          <img src="/img/logo.svg" alt="Hop & Barley logo" width="26" height="38" />
          <span>Hop &amp; Barley</span>
        </Link>
        <nav
          id="primary-navigation"
          className={`main-nav${isMenuOpen ? " is-open" : ""}`}
          aria-label="Main navigation"
        >
          <Link href="/" onClick={() => setIsMenuOpen(false)}>Products</Link>
          <Link href="#guides-recipes" onClick={() => setIsMenuOpen(false)}>Guides &amp; Recipes</Link>
          <Link href="#community" onClick={() => setIsMenuOpen(false)}>Community</Link>
          <Link href="#resources" onClick={() => setIsMenuOpen(false)}>Resources</Link>
          <Link href="#contact" onClick={() => setIsMenuOpen(false)}>Contact</Link>
        </nav>
        {!isReady ? null : user ? (
          <div className="header-actions header-user-actions">
            <Link className="header-icon-link" href="/account" aria-label="My account">
              <img
                className={avatarUrl ? "header-avatar" : undefined}
                src={avatarUrl ?? "/img/icons/User_alt.svg"}
                alt=""
              />
            </Link>
            <Link className="header-icon-link cart-icon-link" href="/cart" aria-label="Shopping cart">
              <img src="/img/icons/Shopping_bag.svg" alt="" />
              <span className="cart-count">{cart.total_quantity}</span>
            </Link>
            <button className="text-button" onClick={logout} type="button">
              Sign out
            </button>
          </div>
        ) : (
          <div className="header-actions header-auth-buttons">
            <Link
              className="header-icon-link cart-icon-link"
              href="/cart"
              aria-label={`Shopping cart, ${cart.total_quantity} items`}
            >
              <img src="/img/icons/Shopping_bag.svg" alt="" />
              <span className="cart-count">{cart.total_quantity}</span>
            </Link>
            <Link className="button button-secondary" href="/login">
              Sign in
            </Link>
            <Link className="button" href="/register">
              Register
            </Link>
          </div>
        )}
        <button
          className={`menu-toggle${isMenuOpen ? " is-open" : ""}`}
          type="button"
          aria-label={isMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={isMenuOpen}
          aria-controls="primary-navigation"
          onClick={() => setIsMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  );
}
