import type {
  Cart,
  Category,
  Order,
  Paginated,
  Product,
  Review,
} from '@/lib/types';

export const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'
).replace(/\/$/, '');

export function getApiUrl(path: string): string {
  return `${apiBaseUrl}/${path.replace(/^\//, '')}`;
}

export function getAssetUrl(path: string | null): string {
  if (!path) {
    return '/img/logo.svg';
  }
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return new URL(path, new URL(apiBaseUrl).origin).toString();
}

async function getPublicJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(getApiUrl(path), {
      next: { revalidate: 60 },
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function getCategories(): Promise<Category[]> {
  return (await getPublicJson<Category[]>('categories/')) ?? [];
}

export async function getProducts(
  searchParams: Record<string, string | string[] | undefined>
): Promise<Paginated<Product> | null> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (typeof value === 'string' && value.trim()) {
      params.set(key, value);
    } else if (Array.isArray(value)) {
      value
        .filter(item => item.trim())
        .forEach(item => params.append(key, item));
    }
  }
  const suffix = params.size ? `?${params.toString()}` : '';
  return getPublicJson<Paginated<Product>>(`products/${suffix}`);
}

export async function getProduct(slug: string): Promise<Product | null> {
  return getPublicJson<Product>(`products/${slug}/`);
}

export async function getReviews(
  slug: string
): Promise<Paginated<Review> | null> {
  return getPublicJson<Paginated<Review>>(`products/${slug}/reviews/`);
}

export type { Cart, Order, Product, Review };
