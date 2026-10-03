import type { Category } from "@/lib/types";

export type CategoryOption = Category & {
  depth: number;
  label: string;
};

/** Convert the API's flat parent-id list into a stable, readable hierarchy. */
export function flattenCategories(categories: Category[]): CategoryOption[] {
  const childrenByParent = new Map<number | null, Category[]>();
  for (const category of categories) {
    const siblings = childrenByParent.get(category.parent) ?? [];
    siblings.push(category);
    childrenByParent.set(category.parent, siblings);
  }
  for (const children of childrenByParent.values()) {
    children.sort((left, right) => left.name.localeCompare(right.name));
  }

  const result: CategoryOption[] = [];
  const visited = new Set<number>();
  const visit = (parentId: number | null, depth: number) => {
    for (const category of childrenByParent.get(parentId) ?? []) {
      if (visited.has(category.id)) {
        continue;
      }
      visited.add(category.id);
      result.push({
        ...category,
        depth,
        label: `${"— ".repeat(depth)}${category.name}`,
      });
      visit(category.id, depth + 1);
    }
  };

  visit(null, 0);
  // An active category whose parent was deactivated remains selectable.
  for (const category of categories) {
    if (!visited.has(category.id)) {
      result.push({ ...category, depth: 0, label: category.name });
      visit(category.id, 1);
    }
  }
  return result;
}
