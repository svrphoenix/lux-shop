"use client";

import { useAuth } from "@/components/auth-provider";
import { createReview, getProductForCurrentUser } from "@/lib/client-api";
import { getAssetUrl } from "@/lib/api";
import type { Product, Review } from "@/lib/types";
import { useEffect, useState } from "react";

type ReviewSectionProps = {
  product: Product;
  initialReviews: Review[];
};

export function ReviewSection({ product, initialReviews }: ReviewSectionProps) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState(initialReviews);
  const [canReview, setCanReview] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!user) {
      return;
    }
    void getProductForCurrentUser(product.slug)
      .then((currentProduct) => setCanReview(Boolean(currentProduct.can_review)))
      .catch(() => setCanReview(false));
  }, [product.slug, user]);

  const submitReview = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage(null);
    try {
      const review = await createReview(product.slug, { rating, comment });
      setReviews((currentReviews) => [review, ...currentReviews]);
      setCanReview(false);
      setComment("");
      setMessage("Thank you for sharing your experience.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to save review.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="reviews-section" aria-labelledby="reviews-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community</p>
          <h2 id="reviews-heading">Latest reviews</h2>
        </div>
        <p className="muted">{product.rating_count} verified reviews</p>
      </div>
      {user && canReview ? (
        <form className="review-form" onSubmit={(event) => void submitReview(event)}>
          <label>
            Rating
            <select value={rating} onChange={(event) => setRating(Number(event.target.value))}>
              {[5, 4, 3, 2, 1].map((value) => (
                <option key={value} value={value}>
                  {value} star{value === 1 ? "" : "s"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Your review
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              rows={4}
              placeholder="What did you brew with it?"
            />
          </label>
          <button className="button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Publishing…" : "Publish review"}
          </button>
        </form>
      ) : user ? (
        <p className="info-panel">
          Reviews are available after a paid, shipped, or delivered purchase.
        </p>
      ) : (
        <p className="info-panel">Sign in after your purchase to leave a review.</p>
      )}
      {message ? <p className="inline-message">{message}</p> : null}
      <div className="reviews-grid">
        {reviews.length ? (
          reviews.map((review) => (
            <article className="review-card" key={review.id}>
              <p className="review-rating" aria-label={`${review.rating} out of 5 stars`}>
                {"★".repeat(review.rating)}
                <span className="empty-stars">{"★".repeat(5 - review.rating)}</span>
              </p>
              {review.comment ? <p>{review.comment}</p> : null}
              <div className="review-author">
                {review.author.avatar ? (
                  <img
                    src={getAssetUrl(review.author.avatar)}
                    alt=""
                    width="32"
                    height="32"
                  />
                ) : (
                  <span className="avatar-placeholder" aria-hidden="true">
                    {review.author.username.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <div>
                  <strong>{review.author.username}</strong>
                  <time dateTime={review.created_at}>
                    {new Intl.DateTimeFormat("en", {
                      dateStyle: "medium",
                    }).format(new Date(review.created_at))}
                  </time>
                </div>
              </div>
            </article>
          ))
        ) : (
          <p className="muted">No reviews yet. Be the first to share your brew.</p>
        )}
      </div>
    </section>
  );
}
