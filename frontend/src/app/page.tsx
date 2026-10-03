import { ProductCard } from "@/components/product-card";
import { getCategories, getProducts } from "@/lib/api";
import { flattenCategories } from "@/lib/category-tree";

type HomePageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const params = await searchParams;
  const [categories, productPage] = await Promise.all([
    getCategories(),
    getProducts(params),
  ]);
  const activeCategory = typeof params.category === "string" ? params.category : "";
  const activeOrdering = typeof params.ordering === "string" ? params.ordering : "-created_at";
  const search = typeof params.search === "string" ? params.search : "";
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
              The catalogue is temporarily unavailable. Confirm that the Django API is running.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
