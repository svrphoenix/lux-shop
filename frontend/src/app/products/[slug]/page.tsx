import { AddToCartButton } from '@/components/add-to-cart-button';
import { ProductImage } from '@/components/product-image';
import { ProductDescription } from '@/components/product-description';
import { ReviewSection } from '@/components/review-section';
import { getProduct, getReviews } from '@/lib/api';
import { notFound } from 'next/navigation';

type ProductPageProps = { params: Promise<{ slug: string }> };

export default async function ProductPage({ params }: ProductPageProps) {
  const { slug } = await params;
  const [product, reviews] = await Promise.all([
    getProduct(slug),
    getReviews(slug),
  ]);
  if (!product) {
    notFound();
  }

  return (
    <div className="page-shell product-page">
      <section className="product-detail">
        <ProductImage
          className="product-detail-image"
          src={product.image}
          alt={product.name}
        />
        <div className="product-detail-copy">
          <p className="eyebrow">{product.category.name}</p>
          <h1>{product.name}</h1>
          <p className="rating">
            ★ {product.rating_avg.toFixed(1)}
            <span className="muted">
              {' '}
              ({product.rating_count}{' '}
              {product.rating_count === 1 ? 'review' : 'reviews'})
            </span>
          </p>
          <ProductDescription text={product.description} />
          <p className="price product-detail-price">${product.price}</p>
          <AddToCartButton
            className="button product-detail-add-button"
            product={product}
          />
        </div>
      </section>
      <section className="product-specifications-section">
        <details className="product-specifications">
          <summary>Product specifications</summary>
          <dl>
            <div>
              <dt>Category</dt>
              <dd>{product.category.name}</dd>
            </div>
            <div>
              <dt>Availability</dt>
              <dd>{product.is_in_stock ? "In stock" : "Out of stock"}</dd>
            </div>
            <div>
              <dt>Stock</dt>
              <dd>
                {product.stock} {product.stock === 1 ? "unit" : "units"}
              </dd>
            </div>
            <div>
              <dt>Rating</dt>
              <dd>
                {product.rating_count
                  ? `${product.rating_avg.toFixed(1)} / 5 (${product.rating_count} ${product.rating_count === 1 ? "review" : "reviews"})`
                  : "No reviews yet"}
              </dd>
            </div>
          </dl>
        </details>
      </section>
      <ReviewSection
        product={product}
        initialReviews={reviews?.results ?? []}
      />
    </div>
  );
}
