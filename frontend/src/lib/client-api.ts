'use client';

import { apiBaseUrl, getApiUrl } from '@/lib/api';
import type {
  Cart,
  DeliveryCity,
  DeliveryStreet,
  DeliveryWarehouse,
  Order,
  Product,
  Review,
  User,
} from '@/lib/types';

const ACCESS_TOKEN_KEY = 'hop-and-barley-access-token';
const REFRESH_TOKEN_KEY = 'hop-and-barley-refresh-token';
const USER_KEY = 'hop-and-barley-user';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
  }
}

function getStoredAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getErrorMessage(payload: unknown): string {
  if (typeof payload === 'string') {
    return payload;
  }
  if (payload && typeof payload === 'object') {
    const details = Object.values(payload as Record<string, unknown>).flat();
    const firstDetail = details.find(detail => typeof detail === 'string');
    if (typeof firstDetail === 'string') {
      return firstDetail;
    }
  }
  return 'The request could not be completed.';
}

function isInvalidTokenResponse(status: number, payload: unknown): boolean {
  return (
    (status === 401 || status === 403) &&
    /given token not valid for any token type|token_not_valid/i.test(
      getErrorMessage(payload),
    )
  );
}

let refreshInProgress: Promise<string | null> | null = null;

async function performTokenRefresh(): Promise<string | null> {
  const refresh = window.localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refresh) {
    clearSession('Your session has expired. Please sign in again.');
    return null;
  }

  const response = await fetch(getApiUrl('auth/refresh/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    if (response.status === 400 || response.status === 401 || response.status === 403) {
      clearSession('Your session has expired. Please sign in again.');
    }
    return null;
  }

  const payload: unknown = await response.json();
  if (
    !payload ||
    typeof payload !== 'object' ||
    !('access' in payload) ||
    typeof payload.access !== 'string' ||
    !payload.access
  ) {
    clearSession('Your session has expired. Please sign in again.');
    throw new ApiError('The token refresh response was invalid.', response.status);
  }

  window.localStorage.setItem(ACCESS_TOKEN_KEY, payload.access);
  if ('refresh' in payload && typeof payload.refresh === 'string') {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, payload.refresh);
  }
  return payload.access;
}

function refreshAccessToken(): Promise<string | null> {
  if (!refreshInProgress) {
    refreshInProgress = performTokenRefresh().finally(() => {
      refreshInProgress = null;
    });
  }
  return refreshInProgress;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retryAfterRefresh = true
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body instanceof FormData) {
    headers.delete('Content-Type');
  } else {
    headers.set('Content-Type', 'application/json');
  }
  const token = getStoredAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(getApiUrl(path), { ...options, headers });
  if (response.status === 401 || response.status === 403) {
    let authPayload: unknown = null;
    try {
      authPayload = await response.clone().json();
    } catch {
      // Authentication responses may have an empty body.
    }
    const invalidToken = isInvalidTokenResponse(response.status, authPayload);
    if (token && retryAfterRefresh && (response.status === 401 || invalidToken)) {
      const refreshedToken = await refreshAccessToken();
      if (refreshedToken) {
        return request<T>(path, options, false);
      }
    } else if (!retryAfterRefresh && (response.status === 401 || invalidToken)) {
      clearSession('Your session has expired. Please sign in again.');
    }
  }

  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      // The API may return an empty response.
    }
    throw new ApiError(getErrorMessage(payload), response.status);
  }
  return (await response.json()) as T;
}

export function getStoredUser(): User | null {
  const rawUser = window.localStorage.getItem(USER_KEY);
  if (!rawUser) {
    return null;
  }
  try {
    return JSON.parse(rawUser) as User;
  } catch {
    return null;
  }
}

export function saveSession(session: {
  access: string;
  refresh: string;
  user: User;
}): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, session.access);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh);
  window.localStorage.setItem(USER_KEY, JSON.stringify(session.user));
  window.dispatchEvent(new Event('hop-and-barley-auth-changed'));
}

export function saveUser(user: User): void {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event('hop-and-barley-auth-changed'));
}

export function clearSession(message?: string): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.dispatchEvent(
    new CustomEvent('hop-and-barley-auth-changed', { detail: { message } }),
  );
}

export async function login(username: string, password: string): Promise<User> {
  const response = await fetch(getApiUrl('auth/login/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new ApiError('Invalid username or password.', response.status);
  }
  const payload = (await response.json()) as {
    access: string;
    refresh: string;
    user: User;
  };
  saveSession(payload);
  return payload.user;
}

export async function register(payload: {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
}): Promise<User> {
  const response = await fetch(getApiUrl('auth/register/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new ApiError(getErrorMessage(await response.json()), response.status);
  }
  const session = (await response.json()) as {
    access: string;
    refresh: string;
    user: User;
  };
  saveSession(session);
  return session.user;
}

export function getCart(): Promise<Cart> {
  return request<Cart>('cart/');
}

export function addCartItem(
  productId: number,
  quantity: number
): Promise<Cart> {
  return request<Cart>('cart/items/', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  });
}

export function updateCartItem(
  itemId: number,
  quantity: number
): Promise<Cart> {
  return request<Cart>(`cart/items/${itemId}/`, {
    method: 'PATCH',
    body: JSON.stringify({ quantity }),
  });
}

export function removeCartItem(itemId: number): Promise<Cart> {
  return request<Cart>(`cart/items/${itemId}/`, { method: 'DELETE' });
}

export function clearCart(): Promise<Cart> {
  return request<Cart>('cart/', { method: 'DELETE' });
}

export function mergeGuestCart(
  items: Array<{ product_id: number; quantity: number }>
): Promise<Cart> {
  return request<Cart>('cart/merge/', {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
}

type SearchResults<T> = { results: T[] };

export function searchDeliveryCities(
  query: string,
  signal?: AbortSignal
): Promise<SearchResults<DeliveryCity>> {
  const params = new URLSearchParams({ q: query });
  return request<SearchResults<DeliveryCity>>(`delivery/cities/?${params}`, {
    signal,
  });
}

export function searchDeliveryWarehouses(
  cityRef: string,
  query: string,
  type: 'branch' | 'postomat',
  signal?: AbortSignal
): Promise<SearchResults<DeliveryWarehouse>> {
  const params = new URLSearchParams({ city: cityRef, q: query, type });
  return request<SearchResults<DeliveryWarehouse>>(
    `delivery/warehouses/?${params}`,
    { signal }
  );
}

export function searchDeliveryStreets(
  cityRef: string,
  query: string,
  signal?: AbortSignal
): Promise<SearchResults<DeliveryStreet>> {
  const params = new URLSearchParams({ city: cityRef, q: query });
  return request<SearchResults<DeliveryStreet>>(`delivery/streets/?${params}`, {
    signal,
  });
}

export function createOrder(data: {
  full_name: string;
  phone: string;
  city: string;
  address: string;
  payment_method: 'card' | 'cash_on_delivery';
}): Promise<Order> {
  return request<Order>('orders/checkout/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getOrders(): Promise<Order[]> {
  return request<Order[]>('orders/');
}

export function updateUserProfile(data: FormData): Promise<User> {
  const profile = {
    phone_number: String(data.get('phone_number') ?? ''),
    address: String(data.get('address') ?? ''),
    birth_day: String(data.get('birth_day') ?? '') || null,
  };
  return request<User>('users/me/', {
    method: 'PATCH',
    body: JSON.stringify({
      first_name: String(data.get('first_name') ?? ''),
      last_name: String(data.get('last_name') ?? ''),
      email: String(data.get('email') ?? ''),
      profile,
    }),
  });
}

export function changePassword(data: {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}): Promise<{ detail: string }> {
  return request<{ detail: string }>('auth/change-password/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getProductForCurrentUser(slug: string): Promise<Product> {
  return request<Product>(`products/${slug}/`);
}

export function createReview(
  slug: string,
  data: { rating: number; comment: string }
): Promise<Review> {
  return request<Review>(`products/${slug}/reviews/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export { apiBaseUrl };
