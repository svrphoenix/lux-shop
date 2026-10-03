"use client";

import { useState } from "react";

const expandableDescriptionLength = 280;

export function ProductDescription({ text }: { text: string }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const description =
    text || "A carefully selected ingredient for your next batch.";
  const canExpand = description.length > expandableDescriptionLength;

  return (
    <div className={`product-description-wrap${isExpanded ? " is-expanded" : ""}`}>
      <p className="product-description">{description}</p>
      {canExpand ? (
        <button
          aria-expanded={isExpanded}
          className="product-description-toggle"
          onClick={() => setIsExpanded((expanded) => !expanded)}
          type="button"
        >
          {isExpanded ? "Read less" : "Read more"}
        </button>
      ) : null}
    </div>
  );
}
