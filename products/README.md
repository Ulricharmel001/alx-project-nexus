# Cart and Checkout System

Cart and checkout functionality for the e-commerce system.

## Features

- Add, update, remove products in cart
- Calculate total price
- Create orders from cart
- Handle inventory reservation
- Process payments

## API Endpoints

### Cart Management
- `GET /api/v1/products/cart/` - Get user's cart
- `GET /api/v1/products/cart/items/` - List cart items
- `POST /api/v1/products/cart/add/` - Add item to cart
- `POST /api/v1/products/cart/update/<item_id>/` - Update item quantity
- `DELETE /api/v1/products/cart/remove/<item_id>/` - Remove item from cart
- `POST /api/v1/products/cart/clear/` - Clear entire cart

### Checkout
- `POST /api/v1/products/checkout/` - Create order from cart

### Payment Processing
- `POST /api/v1/products/purchases/` - Initiate payment for order
- `GET /api/v1/products/purchases/verify/<tx_ref>/` - Verify payment status
