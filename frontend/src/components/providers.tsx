"use client";

import { AuthProvider } from "@/components/auth-provider";
import { CartProvider } from "@/components/cart-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <CartProvider>{children}</CartProvider>
    </AuthProvider>
  );
}
