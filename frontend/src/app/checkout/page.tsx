"use client";

import { useAuth } from "@/components/auth-provider";
import { useCart } from "@/components/cart-provider";
import { CheckoutDeliveryFields } from "@/components/checkout-delivery-fields";
import { ApiError, createOrder } from "@/lib/client-api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function CheckoutPage() {
  const { isReady, user } = useAuth();
  const { cart, clear, isLoading } = useCart();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<
    "card" | "cash_on_delivery"
  >("cash_on_delivery");

  useEffect(() => {
    if (isReady && !user) {
      router.replace("/login?next=/checkout");
    }
  }, [isReady, router, user]);

  const submitCheckout = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage(null);
    const data = new FormData(event.currentTarget);
    const city = String(data.get("city") ?? "");
    const address = String(data.get("address") ?? "");
    const selectedPaymentMethod = String(data.get("payment_method") ?? "");
    if (!city || !address) {
      setMessage("Choose a city and delivery location before placing your order.");
      setIsSubmitting(false);
      return;
    }
    if (
      selectedPaymentMethod !== "card" &&
      selectedPaymentMethod !== "cash_on_delivery"
    ) {
      setMessage("Choose a payment method before placing your order.");
      setIsSubmitting(false);
      return;
    }

    try {
      const order = await createOrder({
        full_name: String(data.get("full_name") ?? ""),
        phone: String(data.get("phone") ?? ""),
        city,
        address,
        payment_method: selectedPaymentMethod,
      });
      await clear();
      router.push(`/account?order=${order.order_number}`);
    } catch (submitError) {
      setMessage(
        submitError instanceof ApiError || submitError instanceof Error
          ? submitError.message
          : "Unable to place your order.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady || isLoading) {
    return <div className="page-shell simple-page"><p>Preparing checkout…</p></div>;
  }
  if (!user) {
    return null;
  }
  if (!cart.items.length) {
    return (
      <div className="page-shell simple-page empty-state">
        <h1>Your cart is empty.</h1>
        <Link className="button" href="/">Browse products</Link>
      </div>
    );
  }

  return (
    <div className="page-shell simple-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Almost there</p>
          <h1>Order details</h1>
        </div>
        <Link href="/cart">Back to cart</Link>
      </div>
      <div className="checkout-layout">
        <form className="checkout-form" onSubmit={(event) => void submitCheckout(event)}>
          <h2>Shipping information</h2>
          <label>
            Full name
            <input defaultValue={`${user.first_name} ${user.last_name}`.trim()} name="full_name" required />
          </label>
          <label>
            Phone number
            <input defaultValue={user.profile.phone_number} name="phone" required type="tel" />
          </label>
          <CheckoutDeliveryFields />
          <fieldset className="payment-method-fields">
            <legend>Payment method</legend>
            <label className="payment-method-option">
              <input
                defaultChecked
                name="payment_method"
                onChange={() => setPaymentMethod("cash_on_delivery")}
                required
                type="radio"
                value="cash_on_delivery"
              />
              <span>
                <strong>Cash on delivery</strong>
                <small>Pay when your order arrives.</small>
              </span>
            </label>
            <label className="payment-method-option">
              <input
                name="payment_method"
                onChange={() => setPaymentMethod("card")}
                required
                type="radio"
                value="card"
              />
              <span>
                <strong>Card (test payment)</strong>
                <small>Simulated payment; no card details are collected.</small>
              </span>
            </label>
          </fieldset>
          {message ? <p className="info-panel error-panel">{message}</p> : null}
          <button className="button" disabled={isSubmitting} type="submit">
            {isSubmitting
              ? paymentMethod === "card"
                ? "Processing payment…"
                : "Placing order…"
              : paymentMethod === "card"
                ? `Pay by card — $${cart.total_amount}`
                : `Place order — $${cart.total_amount}`}
          </button>
        </form>
        <aside className="cart-summary">
          <h2>Order summary</h2>
          {cart.items.map((item) => (
            <div className="summary-line" key={item.id}>
              <span>{item.product.name} × {item.quantity}</span>
              <span>${item.line_total}</span>
            </div>
          ))}
          <div className="summary-total"><span>Total</span><strong>${cart.total_amount}</strong></div>
        </aside>
      </div>
    </div>
  );
}
