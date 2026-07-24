# Lovable Frontend Prompt — Nexus E-Commerce

## Backend Base URL
```
https://alx-project-nexus-1-q1us.onrender.com
```

---

## Authentication & JWT

| Method | Endpoint | Auth | Body / Params | Returns |
|--------|----------|------|---------------|---------|
| POST | `/api/v1/accounts/register/` | No | `{email, first_name, last_name, password, password2}` | `{access, refresh, user, email_verification_required}` |
| POST | `/api/v1/accounts/login/` | No | `{email, password}` | `{access, refresh, user}` |
| POST | `/api/v1/accounts/logout/` | Bearer | `{refresh}` | `{message}` |
| GET | `/api/v1/accounts/user/` | Bearer | — | User object with profile |
| PUT | `/api/v1/accounts/user/` | Bearer | Partial user fields | `{message, data}` |
| GET | `/api/v1/accounts/user/profile/` | Bearer | — | `{bio, profile_picture, phone_number, address}` |
| PUT | `/api/v1/accounts/user/profile/` | Bearer | Partial profile fields | `{message, data}` |
| POST | `/api/v1/accounts/password/change/` | Bearer | `{old_password, new_password, new_password2}` | `{message}` |
| POST | `/api/v1/accounts/password/reset/` | No | `{email}` | `{message}` |
| POST | `/api/v1/accounts/password/reset/confirm/<uidb64>/<token>/` | No | `{password, password2}` | `{message}` |
| POST | `/api/v1/accounts/email/verify/` | No | `{email, code}` | `{message, user}` |
| POST | `/api/v1/accounts/email/resend/` | No | `{email}` | `{message}` |
| GET | `/api/v1/accounts/google/login/` | No | — | `{authorization_url}` |
| GET | `/api/v1/accounts/google/callback/?code=...` | No | Query `code` | `{access, refresh, user}` |
| POST | `/api/v1/accounts/google/callback/` | No | `{code}` | `{access, refresh, user}` |
| POST | `/api/v1/accounts/google/token/` | No | `{token}` | `{access, refresh, user}` |
| POST | `/api/v1/token/refresh/` | No | `{refresh}` | `{access}` |

**Auth header format:** `Authorization: Bearer <access_token>`
**Token lifetimes:** Access = 15 min, Refresh = 7 days
**Pagination format (most list endpoints):** `{ count: number, next: url|null, previous: url|null, results: [...] }`

---

## Products

| Method | Endpoint | Auth | Notes |
|--------|----------|------|-------|
| GET | `/api/v1/products/` | Read-only | Paginated `{count, next, previous, results}`. Query: `?search=&ordering=&page=` |
| GET | `/api/v1/products/<uuid:pk>/` | Read-only | Full product with categories[] (UUID array) |
| GET | `/api/v1/products/search/?q=<query>` | Bearer | Returns flat JSON array (NOT paginated) |
| GET | `/api/v1/products/categories/` | Read-only | Paginated `{count, next, previous, results}` |
| GET | `/api/v1/products/categories/<uuid:pk>/` | Read-only | Category detail |
| GET | `/api/v1/products/categories/tree/` | AllowAny | Returns flat JSON array (NOT paginated), hierarchical via nested `children[]` |
| GET | `/api/v1/products/reviews/` | Read-only | Paginated |
| GET | `/api/v1/products/reviews/<uuid:pk>/` | Read-only | Review detail |

---

## Cart (all require Bearer token)

| Method | Endpoint | Body | Notes |
|--------|----------|------|-------|
| GET | `/api/v1/products/cart/` | — | Returns `{items, total_price}` |
| PUT | `/api/v1/products/cart/` | Cart fields | Update cart |
| GET | `/api/v1/products/cart/items/` | — | List cart items |
| POST | `/api/v1/products/cart/items/` | `{product, quantity}` | Add item |
| GET | `/api/v1/products/cart/items/<uuid:pk>/` | — | Item detail |
| PUT | `/api/v1/products/cart/items/<uuid:pk>/` | `{quantity}` | Update item |
| DELETE | `/api/v1/products/cart/items/<uuid:pk>/` | — | Delete item |
| POST | `/api/v1/products/cart/add/` | `{product_id, quantity}` | Add with inventory check |
| DELETE | `/api/v1/products/cart/remove/<uuid:item_id>/` | — | Remove item |
| POST | `/api/v1/products/cart/update/<uuid:item_id>/` | `{quantity}` | Update quantity |
| POST | `/api/v1/products/cart/clear/` | — | Clear entire cart |

---

## Addresses (Bearer token)

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/v1/products/addresses/` | User's addresses |
| POST | `/api/v1/products/addresses/` | `{street, city, state, country, postal_code, is_default}` |
| GET | `/api/v1/products/addresses/<uuid:pk>/` | Address detail |
| PUT | `/api/v1/products/addresses/<uuid:pk>/` | Update address |
| DELETE | `/api/v1/products/addresses/<uuid:pk>/` | Delete address |

---

## Orders & Checkout (Bearer token)

| Method | Endpoint | Body / Notes |
|--------|----------|-------------|
| POST | `/api/v1/products/checkout/` | `{shipping_address_id}` → creates order, clears cart, returns order |
| GET | `/api/v1/products/orders/` | User's orders (staff sees all) |
| POST | `/api/v1/products/orders/` | Create order manually |
| GET | `/api/v1/products/orders/<uuid:pk>/` | Order detail with items |

---

## Payments (Bearer token)

| Method | Endpoint | Body / Notes |
|--------|----------|-------------|
| POST | `/api/v1/products/purchases/` | `{order_id, first_name, last_name, email}` → returns `{checkout_url, tx_ref, purchase_id}` — **redirect user to checkout_url** (Chapa payment page) |
| GET | `/api/v1/products/purchases/` | List user's purchases |
| GET | `/api/v1/products/purchases/<uuid:pk>/` | Purchase detail |
| GET | `/api/v1/products/purchases/verify/<tx_ref>/` | Verify payment → returns `{status: "completed" \| "pending" \| "failed"}` |
| POST | `/api/v1/products/payment-test/` | `{order_id, first_name, last_name, email}` — test endpoint |

---

## Inventory (Bearer token)

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/v1/products/inventory/` | All inventory items |
| GET | `/api/v1/products/inventory/<uuid:pk>/` | Inventory detail |

---

## Data Models

### User
```
{
  id, email, first_name, last_name, role ("admin"|"user"),
  is_active, date_joined,
  profile: { bio, profile_picture, phone_number, address }
}
```

### Product
```
{
  id (uuid), name, description, price (decimal string),
  categories: [uuid...],
  is_active, created_at, updated_at
}
```

### Category
```
{
  id (uuid), name, parent (uuid|null), children: [...],
  created_at, updated_at
}
```

### Cart
```
{
  id (uuid), customer (uuid),
  items: [{ id, product, product_name, product_price, quantity, subtotal, created_at }],
  total_price
}
```

### Address
```
{
  id (uuid), street, city, state, country, postal_code,
  is_default, created_at
}
```

### Order
```
{
  id (uuid), customer (uuid), status ("pending"|"paid"|"shipped"|"delivered"|"cancelled"),
  total_price, currency, shipping_address (uuid),
  items: [{ product, quantity, unit_price_at_purchase, subtotal }],
  created_at
}
```

### Review
```
{
  id (uuid), product (uuid), rating (1-5), title, comment,
  customer, created_at
}
```

---

## Design Requirements

### Color Palette
- **Primary:** Deep Indigo `#4F46E5`
- **Secondary:** Warm Amber `#F59E0B`
- **Background:** Light Slate `#F8FAFC`
- **Surface:** White `#FFFFFF`
- **Text:** Dark Slate `#1E293B`
- **Accent:** Emerald `#10B981`
- **Danger:** Rose `#E11D48`
- Use gradients & shadows extensively throughout

### Responsiveness (Mobile-First)
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Cart: sidebar on desktop (`lg+`), full-page overlay on mobile
- Product grid: 2 cols mobile, 3 tablet, 4 desktop
- Navbar collapses to hamburger on mobile

### Animations (Framer Motion)
- Page transitions: fade + slight slide up
- Stagger children for list appearances
- Hover scale on product cards (`scale: 1.03`)
- Shimmer/skeleton loading states for all data fetching
- Slide-in cart sidebar from right
- Toast notifications (bottom-right) for: "Added to cart", "Order placed", "Payment successful", errors
- Pulse animation on cart badge when item added
- Smooth accordion for category filters
- Spinning loader on all buttons during API calls

### UX Requirements
- **Loading:** Skeleton shimmer on every page/component that fetches data
- **Optimistic updates:** Cart quantity changes reflect instantly, revert on error
- **Debounced search** (300ms) on product search
- **6-digit code inputs** (6 individual boxes) for email verification
- **Instant form validation** with error messages under fields
- **Toast notifications** for all success/error actions
- **Cart badge** on navbar icon showing item count
- **Confirmation modal** before clearing cart or placing order
- **Payment redirect:** After checkout, show order summary then redirect to Chapa checkout_url
- **Poll for payment status** after redirect back from Chapa (poll `/verify/<tx_ref>` every 3s until completed/failed)

### Pages
1. **Home** — Hero section with gradient CTA, featured products grid, category showcase
2. **Products** — Grid with search bar, category sidebar filter, sort dropdown, pagination
3. **Product Detail** — Image area, product info, quantity selector, add-to-cart button, reviews section
4. **Cart** — Item list with qty controls, remove button, total, proceed to checkout CTA
5. **Checkout** — Address selection/create, order summary, place order button → redirects to Chapa
6. **Orders** — List of past orders with status badges, click for detail
7. **Order Detail** — Full order info, items table, payment status, tracking
8. **Profile** — View/edit personal info, profile picture upload, change password
9. **Login** — Email + password form, Google OAuth button, link to register
10. **Register** — Name, email, password, confirm password, Google OAuth
11. **Forgot Password** — Email input, success message
12. **Reset Password** — New password + confirm (uid/token from URL)
13. **Email Verification** — 6-digit code input after register

### Tech Stack
- React 18+ with Vite
- TypeScript
- Tailwind CSS v4
- Framer Motion
- React Query (TanStack Query) for server state & caching
- React Router v7
- React Hook Form + Zod for forms
- Axios or fetch
- Lazy load images (`loading="lazy"`)
- Code-split routes with `React.lazy()`
- Preload product images on card hover

### Performance
- Lazy load images
- Code-split route components
- Cache API responses with React Query (staleTime: 5min for products, 30s for cart)
- Debounce search input
- Preload product detail images on card hover
- Use `will-change` for animated elements
- Memoize heavy computations
