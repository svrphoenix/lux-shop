"use client";

import { useAuth } from "@/components/auth-provider";
import { AccountProfileForm } from "@/components/account-profile-form";
import { cancelOrder, getOrders } from "@/lib/client-api";
import type { Order } from "@/lib/types";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

const orderStatusLabel: Record<Order["status"], string> = {
  pending: "Pending",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

const orderStatuses: Order["status"][] = [
  "pending",
  "paid",
  "shipped",
  "delivered",
  "cancelled",
];

export default function AccountPage() {
  return (
    <Suspense fallback={<div className="page-shell simple-page"><p>Loading your account…</p></div>}>
      <AccountContent />
    </Suspense>
  );
}

function AccountContent() {
  const { isReady, user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedStatus = searchParams.get("status") ?? "";
  const isSelectedStatusValid = orderStatuses.includes(
    selectedStatus as Order["status"],
  );
  const [orderState, setOrderState] = useState<{
    status: string;
    orders?: Order[];
    error?: string;
  } | null>(null);
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [orderPendingCancellation, setOrderPendingCancellation] = useState<
    string | null
  >(null);
  const [cancellationNotice, setCancellationNotice] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const currentOrderState =
    orderState?.status === selectedStatus ? orderState : null;
  const orders = currentOrderState?.orders ?? null;
  const error = currentOrderState?.error ?? null;

  useEffect(() => {
    if (!cancellationNotice) {
      return;
    }
    const timeout = window.setTimeout(() => setCancellationNotice(null), 5000);
    return () => window.clearTimeout(timeout);
  }, [cancellationNotice]);

  useEffect(() => {
    if (isReady && !user) {
      router.replace("/login?next=/account");
    }
  }, [isReady, router, user]);

  useEffect(() => {
    if (!user) {
      return;
    }
    const controller = new AbortController();
    void getOrders(selectedStatus || undefined, controller.signal)
      .then((loadedOrders) =>
        setOrderState({ status: selectedStatus, orders: loadedOrders }),
      )
      .catch((loadError) => {
        if (!controller.signal.aborted) {
          setOrderState({
            status: selectedStatus,
            error:
              loadError instanceof Error
                ? loadError.message
                : "Unable to load orders.",
          });
        }
      });
    return () => controller.abort();
  }, [selectedStatus, user]);

  const updateOrderStatus = (status: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (status) {
      params.set("status", status);
    } else {
      params.delete("status");
    }
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  const handleCancelOrder = async (order: Order) => {
    setCancellingOrder(order.order_number);
    setCancellationNotice(null);
    try {
      const cancelledOrder = await cancelOrder(order.order_number);
      setOrderState((current) => {
        if (current?.status !== selectedStatus || !current.orders) {
          return current;
        }
        const updatedOrders = current.orders
          .map((currentOrder) =>
            currentOrder.order_number === cancelledOrder.order_number
              ? cancelledOrder
              : currentOrder,
          )
          .filter(
            (currentOrder) =>
              !selectedStatus || currentOrder.status === selectedStatus,
          );
        return { ...current, orders: updatedOrders };
      });
      setOrderPendingCancellation(null);
      setCancellationNotice({
        type: "success",
        message: `Order #${order.order_number} was cancelled and its quantities were returned to stock.`,
      });
    } catch (cancelError) {
      setOrderPendingCancellation(null);
      setCancellationNotice({
        type: "error",
        message:
          cancelError instanceof Error
            ? cancelError.message
            : "Unable to cancel this order.",
      });
    } finally {
      setCancellingOrder(null);
    }
  };

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
        {cancellationNotice ? (
          <div
            className={`order-toast order-toast-${cancellationNotice.type}`}
            role={cancellationNotice.type === "error" ? "alert" : "status"}
          >
            <span>{cancellationNotice.message}</span>
            <button
              aria-label="Dismiss notification"
              onClick={() => setCancellationNotice(null)}
              type="button"
            >
              ×
            </button>
          </div>
        ) : null}
        <label className="order-status-filter">
          Filter by status
          <select
            value={selectedStatus}
            onChange={(event) => updateOrderStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            {selectedStatus && !isSelectedStatusValid ? (
              <option value={selectedStatus} disabled>
                Invalid status in URL
              </option>
            ) : null}
            {orderStatuses.map((status) => (
              <option key={status} value={status}>
                {orderStatusLabel[status]}
              </option>
            ))}
          </select>
        </label>
        {error ? <p className="info-panel error-panel">{error}</p> : null}
        {orders === null && !error ? <p>Loading orders…</p> : null}
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
                {order.status === "pending" ? (
                  <div className="order-card-actions">
                    {orderPendingCancellation === order.order_number ? (
                      <div
                        className="order-cancel-confirmation"
                        role="group"
                        aria-label={`Confirm cancellation of order ${order.order_number}`}
                      >
                        <p>
                          Cancel order #{order.order_number}? The reserved quantities
                          will be returned to stock.
                        </p>
                        <button
                          className="button button-secondary"
                          disabled={cancellingOrder !== null}
                          onClick={() => setOrderPendingCancellation(null)}
                          type="button"
                        >
                          Keep order
                        </button>
                        <button
                          className="button button-danger"
                          disabled={cancellingOrder !== null}
                          onClick={() => void handleCancelOrder(order)}
                          type="button"
                        >
                          {cancellingOrder === order.order_number
                            ? "Cancelling…"
                            : "Confirm cancellation"}
                        </button>
                      </div>
                    ) : (
                      <button
                        className="button button-secondary"
                        disabled={cancellingOrder !== null}
                        onClick={() =>
                          setOrderPendingCancellation(order.order_number)
                        }
                        type="button"
                      >
                        Cancel order
                      </button>
                    )}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : orders ? (
          <p className="info-panel">
            {selectedStatus
              ? "No orders found with this status."
              : "You have not placed an order yet."}
          </p>
        ) : null}
      </section>
    </div>
  );
}
