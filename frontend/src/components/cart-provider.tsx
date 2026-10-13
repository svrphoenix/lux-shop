"use client";

import {
  addCartItem,
  clearCart as requestClearCart,
  getCart,
  mergeGuestCart,
  removeCartItem,
  updateCartItem,
} from "@/lib/client-api";
import type { Cart, CartItem, CartProduct } from "@/lib/types";
import { useAuth } from "@/components/auth-provider";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const GUEST_CART_KEY = "hop-and-barley-guest-cart";
const emptyCart: Cart = {
  items: [],
  total_quantity: 0,
  total_amount: "0.00",
  updated_at: null,
};

type CartContextValue = {
  cart: Cart;
  isLoading: boolean;
  error: string | null;
  addProduct: (product: CartProduct, quantity?: number) => Promise<void>;
  setQuantity: (item: CartItem, quantity: number) => Promise<void>;
  removeItem: (item: CartItem) => Promise<void>;
  clear: () => Promise<void>;
};

const CartContext = createContext<CartContextValue | null>(null);

function hydrateGuestCart(): Cart {
  try {
    const storedCart = window.localStorage.getItem(GUEST_CART_KEY);
    return storedCart ? (JSON.parse(storedCart) as Cart) : emptyCart;
  } catch {
    return emptyCart;
  }
}

function persistGuestCart(cart: Cart): void {
  window.localStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
}

function getGuestCartWithItems(items: CartItem[]): Cart {
  const totalQuantity = items.reduce((total, item) => total + item.quantity, 0);
  const total = items.reduce(
    (sum, item) => sum + Number(item.product.price) * item.quantity,
    0,
  );
  return {
    items,
    total_quantity: totalQuantity,
    total_amount: total.toFixed(2),
    updated_at: new Date().toISOString(),
  };
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const { isReady, user } = useAuth();
  const [cart, setCart] = useState<Cart>(emptyCart);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshForUser = useCallback(async () => {
    const guestCart = hydrateGuestCart();
    if (guestCart.items.length) {
      const mergedCart = await mergeGuestCart(
        guestCart.items.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        })),
      );
      window.localStorage.removeItem(GUEST_CART_KEY);
      setCart(mergedCart);
      return;
    }
    setCart(await getCart());
  }, []);

  useEffect(() => {
    if (!isReady) {
      return;
    }
    const loadCart = async () => {
      setIsLoading(true);
      setError(null);
      try {
        if (user) {
          await refreshForUser();
        } else {
          setCart(hydrateGuestCart());
        }
      } catch (loadError) {
        setError(
          loadError instanceof Error ? loadError.message : "Unable to load cart.",
        );
      } finally {
        setIsLoading(false);
      }
    };
    void loadCart();
  }, [isReady, refreshForUser, user]);

  const addProduct = useCallback(
    async (product: CartProduct, quantity = 1) => {
      setError(null);
      if (user) {
        setCart(await addCartItem(product.id, quantity));
        return;
      }
      const existingItem = cart.items.find(
        (item) => item.product.id === product.id,
      );
      const requestedQuantity = (existingItem?.quantity ?? 0) + quantity;
      if (requestedQuantity > product.stock) {
        throw new Error(`Only ${product.stock} units are available.`);
      }
      const nextItems = existingItem
        ? cart.items.map((item) =>
            item.product.id === product.id
              ? {
                  ...item,
                  quantity: requestedQuantity,
                  line_total: (Number(product.price) * requestedQuantity).toFixed(2),
                }
              : item,
          )
        : [
            ...cart.items,
            {
              id: -product.id,
              product,
              quantity,
              line_total: (Number(product.price) * quantity).toFixed(2),
            },
          ];
      const nextCart = getGuestCartWithItems(nextItems);
      persistGuestCart(nextCart);
      setCart(nextCart);
    },
    [cart, user],
  );

  const setQuantity = useCallback(
    async (item: CartItem, quantity: number) => {
      setError(null);
      if (user) {
        setCart(await updateCartItem(item.id, quantity));
        return;
      }
      if (quantity > item.product.stock) {
        throw new Error(`Only ${item.product.stock} units are available.`);
      }
      const nextItems = cart.items
        .map((cartItem) =>
          cartItem.id === item.id
            ? {
                ...cartItem,
                quantity,
                line_total: (Number(cartItem.product.price) * quantity).toFixed(2),
              }
            : cartItem,
        )
        .filter((cartItem) => cartItem.quantity > 0);
      const nextCart = getGuestCartWithItems(nextItems);
      persistGuestCart(nextCart);
      setCart(nextCart);
    },
    [cart.items, user],
  );

  const removeItem = useCallback(
    async (item: CartItem) => {
      setError(null);
      if (user) {
        setCart(await removeCartItem(item.id));
        return;
      }
      const nextCart = getGuestCartWithItems(
        cart.items.filter((cartItem) => cartItem.id !== item.id),
      );
      persistGuestCart(nextCart);
      setCart(nextCart);
    },
    [cart.items, user],
  );

  const clear = useCallback(async () => {
    setError(null);
    if (user) {
      setCart(await requestClearCart());
      return;
    }
    window.localStorage.removeItem(GUEST_CART_KEY);
    setCart(emptyCart);
  }, [user]);

  const value = useMemo(
    () => ({ cart, isLoading, error, addProduct, setQuantity, removeItem, clear }),
    [addProduct, cart, clear, error, isLoading, removeItem, setQuantity],
  );
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used inside CartProvider.");
  }
  return context;
}
