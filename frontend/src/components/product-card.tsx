'use client';

import { AddToCartButton } from '@/components/add-to-cart-button';
import { ProductImage } from '@/components/product-image';
import type { Product } from '@/lib/types';
import Link from 'next/link';

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="product-card">
      <Link
        aria-label={`View ${product.name}`}
        className="product-card-link"
        href={`/products/${product.slug}`}
      />
      <div className="product-image-frame">
        <ProductImage
          className="product-image"
          src={product.image}
          alt=""
        />
      </div>
      <div className="product-card-body">
        <p className="eyebrow">{product.category.name}</p>
        <h2>{product.name}</h2>
        <div
          className="rating"
          aria-label={`${product.rating_avg} out of 5 stars`}
        >
          <span>★</span> {product.rating_avg.toFixed(1)}
          <span className="muted"> ({product.rating_count})</span>
        </div>
        <p className="product-card-description">{product.description}</p>
        <div className="product-card-bottom">
          <strong className="price">${product.price}</strong>
          <AddToCartButton product={product} />
        </div>
      </div>
    </article>
  );
}
