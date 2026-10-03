"use client";

import { useAuth } from "@/components/auth-provider";
import { useCart } from "@/components/cart-provider";
import { ProductImage } from "@/components/product-image";
import Link from "next/link";
import { useState } from "react";

export default function CartPage() {
  const { user } = useAuth();
  const { cart, error, isLoading, removeItem, setQuantity } = useCart();
  const [updatingItemId, setUpdatingItemId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const changeQuantity = async (itemId: number, quantity: number) => {
    const item = cart.items.find((currentItem) => currentItem.id === itemId);
    if (!item) {
      return;
    }
    setUpdatingItemId(itemId);
    setMessage(null);
    try {
      await setQuantity(item, quantity);
    } catch (changeError) {
      setMessage(
        changeError instanceof Error ? changeError.message : "Unable to update cart.",
      );
    } finally {
      setUpdatingItemId(null);
    }
  };

  const remove = async (itemId: number) => {
    const item = cart.items.find((currentItem) => currentItem.id === itemId);
    if (!item) {
      return;
    }
    setUpdatingItemId(itemId);
    setMessage(null);
    try {
      await removeItem(item);
    } catch (removeError) {
      setMessage(
        removeError instanceof Error ? removeError.message : "Unable to remove item.",
      );
    } finally {
      setUpdatingItemId(null);
    }
  };

  if (isLoading) {
    return <div className="page-shell simple-page"><p>Loading your cart…</p></div>;
  }

  return (
    <div className="page-shell simple-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Your selection</p>
          <h1>Shopping cart</h1>
        </div>
        <span className="muted">{cart.total_quantity} item(s)</span>
      </div>
      {!user ? (
        <p className="info-panel">
          Your cart is saved in this browser. <Link href="/login">Sign in</Link> to
          keep it with your account and complete checkout.
        </p>
      ) : null}
      {error || message ? <p className="info-panel error-panel">{error ?? message}</p> : null}
      {cart.items.length ? (
        <div className="cart-layout">
          <section className="cart-items">
            {cart.items.map((item) => (
              <article className="cart-item" key={item.id}>
                <ProductImage src={item.product.image} alt={item.product.name} />
                <div className="cart-item-details">
                  <Link href={`/products/${item.product.slug}`}>
                    <h2>{item.product.name}</h2>
                  </Link>
                  <p className="muted">${item.product.price} each</p>
                  <div className="quantity-control" aria-label={`Quantity for ${item.product.name}`}>
                    <button
                      aria-label="Decrease quantity"
                      disabled={updatingItemId === item.id}
                      onClick={() => void changeQuantity(item.id, item.quantity - 1)}
                      type="button"
                    >
                      −
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      aria-label="Increase quantity"
                      disabled={updatingItemId === item.id || item.quantity >= item.product.stock}
                      onClick={() => void changeQuantity(item.id, item.quantity + 1)}
                      type="button"
                    >
                      +
                    </button>
                  </div>
                </div>
                <div className="cart-item-total">
                  <strong>${item.line_total}</strong>
                  <button
                    className="text-button danger-button"
                    disabled={updatingItemId === item.id}
                    onClick={() => void remove(item.id)}
                    type="button"
                  >
                    Remove
                  </button>
                </div>
              </article>
            ))}
          </section>
          <aside className="cart-summary">
            <h2>Order summary</h2>
            <div><span>Items</span><span>{cart.total_quantity}</span></div>
            <div className="summary-total"><span>Total</span><strong>${cart.total_amount}</strong></div>
            {user ? (
              <Link className="button button-wide" href="/checkout">Proceed to checkout</Link>
            ) : (
              <Link className="button button-wide" href="/login?next=/checkout">Sign in to checkout</Link>
            )}
          </aside>
        </div>
      ) : (
        <div className="empty-state">
          <h2>Your cart is empty.</h2>
          <p>Find the ingredients for your next batch.</p>
          <Link className="button" href="/">Browse products</Link>
        </div>
      )}
    </div>
  );
}
