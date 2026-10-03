"use client";

import { useAuth } from "@/components/auth-provider";
import { AccountProfileForm } from "@/components/account-profile-form";
import { getOrders } from "@/lib/client-api";
import type { Order } from "@/lib/types";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

const orderStatusLabel: Record<Order["status"], string> = {
  pending: "Pending",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export default function AccountPage() {
  return (
    <Suspense fallback={<div className="page-shell simple-page"><p>Loading your account…</p></div>}>
      <AccountContent />
    </Suspense>
  );
}

function AccountContent() {
  const { isReady, user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isReady && !user) {
      router.replace("/login?next=/account");
    }
  }, [isReady, router, user]);

  useEffect(() => {
    if (!user) {
      return;
    }
    void getOrders()
      .then(setOrders)
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "Unable to load orders."),
      );
  }, [user]);

  if (!isReady || !user) {
    return <div className="page-shell simple-page"><p>Loading your account…</p></div>;
  }

  const placedOrder = searchParams.get("order");
  return (
    <div className="page-shell simple-page">
      <p className="eyebrow">My account</p>
      <h1>Welcome, {user.first_name || user.username}</h1>
      <p className="muted">{user.email}</p>
      {placedOrder ? (
        <p className="info-panel success-panel">
          Your order #{placedOrder} has been placed. Thank you for choosing Hop &amp; Barley.
        </p>
      ) : null}
      <div className="account-settings-grid">
        <AccountProfileForm />
        <aside className="account-security-card">
          <div>
            <p className="eyebrow">Security</p>
            <h2>Password</h2>
            <p className="muted">Update your password separately from your profile details.</p>
          </div>
          <Link className="button button-secondary" href="/account/password">
            Change password
          </Link>
        </aside>
      </div>
      <section className="orders-section">
        <div className="section-heading"><h2>Orders</h2><Link href="/">Continue shopping</Link></div>
        {error ? <p className="info-panel error-panel">{error}</p> : null}
        {orders === null ? <p>Loading orders…</p> : null}
        {orders?.length ? (
          <div className="order-list">
            {orders.map((order) => (
              <article className="order-card" key={order.order_number}>
                <details className="order-details">
                  <summary>
                    <span className="order-summary-main">
                      <strong>Order #{order.order_number}</strong>
                      <time dateTime={order.created_at}>
                        {new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(
                          new Date(order.created_at),
                        )}
                      </time>
                    </span>
                    <span className={`status status-${order.status}`}>
                      {orderStatusLabel[order.status]}
                    </span>
                    <strong className="order-summary-total">${order.total_amount}</strong>
                  </summary>
                  <div className="order-details-content">
                    <h3 className="order-items-heading">Items:</h3>
                    <ul className="order-items">
                      {order.items.map((item) => (
                        <li key={item.id}>
                          <Link href={`/products/${item.product.slug}`}>
                            {item.product.name}
                          </Link>
                          <span className="order-item-quantity">
                            {item.quantity} × ${item.price}
                          </span>
                          <strong>${item.cost}</strong>
                        </li>
                      ))}
                    </ul>
                    <div className="order-details-total">
                      <span>Total</span>
                      <strong>${order.total_amount}</strong>
                    </div>
                    <dl className="order-shipping-details">
                      <div>
                        <dt>Payment</dt>
                        <dd>
                          {order.payment
                            ? `${order.payment.method === "card" ? "Card" : "Cash on delivery"} · ${order.payment.status === "succeeded" ? "Paid" : order.payment.status === "failed" ? "Failed" : "Pending"} · ${order.payment.amount} ${order.payment.currency}${order.payment.is_mock ? " (test)" : ""}`
                            : "Payment details unavailable"}
                        </dd>
                      </div>
                      <div>
                        <dt>Delivery address</dt>
                        <dd>{order.shipping_address}</dd>
                      </div>
                      <div>
                        <dt>Contact phone</dt>
                        <dd>{order.customer_phone}</dd>
                      </div>
                      <div>
                        <dt>Contact email</dt>
                        <dd>{order.customer_email}</dd>
                      </div>
                    </dl>
                  </div>
                </details>
              </article>
            ))}
          </div>
        ) : orders ? <p className="info-panel">You have not placed an order yet.</p> : null}
      </section>
    </div>
  );
}
