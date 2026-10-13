"use client";

import { useCart } from "@/components/cart-provider";
import type { Product } from "@/lib/types";
import { useState } from "react";

export function AddToCartButton({
  product,
  className = "button",
}: {
  product: Product;
  className?: string;
}) {
  const { addProduct } = useCart();
  const [message, setMessage] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);

  const addToCart = async () => {
    setIsAdding(true);
    setMessage(null);
    try {
      await addProduct(
        {
          id: product.id,
          name: product.name,
          slug: product.slug,
          price: product.price,
          image: product.image,
          stock: product.stock,
          is_active: true,
        },
        1,
      );
      setMessage("Added to cart.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to add item.");
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div>
      <button
        className={className}
        type="button"
        disabled={!product.is_in_stock || isAdding}
        onClick={() => void addToCart()}
      >
        {product.is_in_stock ? (isAdding ? "Adding…" : "Add to cart") : "Out of stock"}
      </button>
      {message ? <p className="inline-message">{message}</p> : null}
    </div>
  );
}
