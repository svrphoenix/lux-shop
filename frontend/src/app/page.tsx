import { ProductCard } from "@/components/product-card";
import { getCategories, getProducts } from "@/lib/api";
import { flattenCategories } from "@/lib/category-tree";
import Link from "next/link";

const defaultProductPageSize = 6;

type HomePageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function getPageHref(
  searchParams: Record<string, string | string[] | undefined>,
  page: number,
): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (key === "page") {
      continue;
    }
    if (typeof value === "string" && value.trim()) {
      params.set(key, value);
    } else if (Array.isArray(value)) {
      value
        .filter((item) => item.trim())
        .forEach((item) => params.append(key, item));
    }
  }
  params.set("page", String(page));
  return `/?${params.toString()}`;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const params = await searchParams;
  const [categories, productPage] = await Promise.all([
    getCategories(),
    getProducts(params),
  ]);
  const activeCategory = typeof params.category === "string" ? params.category : "";
  const activeOrdering = typeof params.ordering === "string" ? params.ordering : "-created_at";
  const search = typeof params.search === "string" ? params.search : "";
  const currentPage =
    typeof params.page === "string" && Number.isInteger(Number(params.page))
      ? Math.max(1, Number(params.page))
      : 1;
  const pageSize =
    typeof params.page_size === "string" && Number(params.page_size) > 0
      ? Math.min(100, Number(params.page_size))
      : defaultProductPageSize;
  const pageCount = productPage
    ? Math.max(1, Math.ceil(productPage.count / pageSize))
    : 1;
  const categoryOptions = flattenCategories(categories);

  return (
    <div className="page-shell catalogue-page">
      <section className="catalogue-hero">
        <p className="eyebrow">Brewing ingredients</p>
        <h1>Build your next great beer.</h1>
        <p>Fresh hops, reliable yeast, and carefully selected malt for every batch.</p>
      </section>
      <section className="catalogue-layout" aria-label="Product catalogue">
        <aside className="filters-panel">
          <form action="/" className="filters-form">
            <label>
              Search
              <input defaultValue={search} name="search" placeholder="Hops, yeast, malt…" />
            </label>
            <label>
              Category
              <select defaultValue={activeCategory} name="category">
                <option value="">All ingredients</option>
                {categoryOptions.map((category) => (
                  <option key={category.id} value={category.slug}>
                    {category.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="price-inputs">
              <label>
                Minimum price
                <input defaultValue={params.min_price} min="0" name="min_price" step="0.01" type="number" />
              </label>
              <label>
                Maximum price
                <input defaultValue={params.max_price} min="0" name="max_price" step="0.01" type="number" />
              </label>
            </div>
            <label className="checkbox-label">
              <input defaultChecked={params.in_stock === "true"} name="in_stock" type="checkbox" value="true" />
              In stock only
            </label>
            <label>
              Sort by
              <select defaultValue={activeOrdering} name="ordering">
                <option value="-created_at">Newest</option>
                <option value="price">Price: low to high</option>
                <option value="-price">Price: high to low</option>
                <option value="-rating">Rating</option>
                <option value="-popularity">Most popular</option>
              </select>
            </label>
            <button className="button" type="submit">Apply filters</button>
          </form>
        </aside>
        <div>
          <div className="section-heading catalogue-result-heading">
            <h2>{productPage ? `${productPage.count} products` : "Catalogue"}</h2>
          </div>
          {productPage ? (
            productPage.results.length ? (
              <div className="product-grid">
                {productPage.results.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            ) : (
              <p className="info-panel">No ingredients match these filters.</p>
            )
          ) : (
            <p className="info-panel error-panel">
              Unfortunately the catalogue is temporarily unavailable.
            </p>
          )}
          {productPage && pageCount > 1 ? (
            <nav className="catalogue-pagination" aria-label="Product pages">
              {productPage.previous ? (
                <Link
                  className="button button-secondary"
                  href={getPageHref(params, currentPage - 1)}
                  rel="prev"
                >
                  Previous
                </Link>
              ) : (
                <span />
              )}
              <span aria-current="page">
                Page {currentPage} of {pageCount}
              </span>
              {productPage.next ? (
                <Link
                  className="button button-secondary"
                  href={getPageHref(params, currentPage + 1)}
                  rel="next"
                >
                  Next
                </Link>
              ) : (
                <span />
              )}
            </nav>
          ) : null}
        </div>
      </section>
    </div>
  );
}
