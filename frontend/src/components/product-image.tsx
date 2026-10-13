import { getAssetUrl } from "@/lib/api";

export function ProductImage({
  src,
  alt,
  className,
}: {
  src: string | null;
  alt: string;
  className?: string;
}) {
  return (
    <img
      className={`${className ?? ""}${src ? "" : " product-image-fallback"}`}
      src={getAssetUrl(src)}
      alt={alt}
    />
  );
}
