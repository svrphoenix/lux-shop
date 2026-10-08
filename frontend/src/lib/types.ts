export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
  parent: number | null;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string;
  category: Category;
  image: string | null;
  stock: number;
  is_in_stock: boolean;
  rating_avg: number;
  rating_count: number;
  sold_qty: number;
  created_at: string;
  can_review?: boolean;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type User = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile: {
    phone_number: string;
    address: string;
    birth_day: string | null;
    avatar: string | null;
    avatar_preset: string;
  };
};

export type AuthTokens = {
  access: string;
  refresh: string;
};

export type Review = {
  id: number;
  rating: number;
  comment: string;
  author: {
    username: string;
    avatar: string | null;
    avatar_preset: string;
  };
  created_at: string;
  updated_at: string;
};

export type DeliveryCity = {
  ref: string;
  name: string;
  area: string;
  delivery_city_ref: string;
  label: string;
};

export type DeliveryWarehouse = {
  ref: string;
  city_ref: string;
  city_name: string;
  number: string;
  name: string;
  is_postomat: boolean;
};

export type DeliveryStreet = {
  ref: string;
  name: string;
  street_type: string;
  label: string;
};

export type CartProduct = Pick<
  Product,
  "id" | "name" | "slug" | "price" | "image" | "stock"
> & { is_active: boolean };

export type CartItem = {
  id: number;
  product: CartProduct;
  quantity: number;
  line_total: string;
};

export type Cart = {
  items: CartItem[];
  total_quantity: number;
  total_amount: string;
  updated_at: string | null;
};

export type Order = {
  order_number: string;
  status: "pending" | "paid" | "shipped" | "delivered" | "cancelled";
  customer_email: string;
  customer_first_name: string;
  customer_last_name: string;
  customer_phone: string;
  shipping_address: string;
  total_amount: string;
  payment: {
    method: "card" | "cash_on_delivery";
    status: "pending" | "succeeded" | "failed";
    amount: string;
    currency: string;
    transaction_reference: string | null;
    is_mock: boolean;
    created_at: string;
  } | null;
  items: Array<{
    id: number;
    product: Pick<CartProduct, "id" | "name" | "slug" | "image">;
    price: string;
    quantity: number;
    cost: string;
  }>;
  created_at: string;
};
