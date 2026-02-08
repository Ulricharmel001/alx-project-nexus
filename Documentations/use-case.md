# E-Commerce Platform Use Cases - Simplified

This document explains how different users interact with the e-commerce platform.

## Customer Use Cases

### 1. Create Account
**Who:** New customer
**What:** Sign up for an account
**How:**
- Enter email and password
- Verify email through confirmation link
- Account is activated

### 2. Log In
**Who:** Registered customer
**What:** Access account
**How:**
- Enter email and password
- Receive authentication token
- Access protected features

### 3. Browse Products
**Who:** Customer or Guest
**What:** Look at available products
**How:**
- View product listings
- Filter by category, price, or other features
- Click on products to see details

### 4. Search for Products
**Who:** Customer or Guest
**What:** Find specific items
**How:**
- Type keywords in search bar
- See matching products
- Refine results with filters

### 5. Add to Cart
**Who:** Customer or Guest
**What:** Put items in shopping cart
**How:**
- Select product and quantity
- Click "Add to Cart"
- Item appears in cart

### 6. Update Cart
**Who:** Customer or Guest
**What:** Change cart contents
**How:**
- Go to cart page
- Increase/decrease quantities or remove items
- Cart updates automatically

### 7. Checkout
**Who:** Customer
**What:** Complete purchase
**How:**
- Review cart items
- Enter shipping address
- Choose shipping method
- Enter payment information
- Confirm order
- Receive confirmation

### 8. Track Order
**Who:** Customer
**What:** Check order status
**How:**
- Go to account order history
- View order status (pending, shipped, delivered)
- See tracking information if available

### 9. Leave Review
**Who:** Customer
**What:** Rate and review purchased products
**How:**
- Go to purchased product
- Rate with 1-5 stars
- Optionally write comment
- Submit review

### 10. Manage Profile
**Who:** Customer
**What:** Update personal information
**How:**
- Go to profile settings
- Edit name, phone, or avatar
- Save changes

## Admin Use Cases

### 1. Add Product
**Who:** Administrator
**What:** Add new items to store
**How:**
- Go to product management
- Fill product details (name, description, price)
- Upload images
- Set category and stock level
- Publish product

### 2. Update Product
**Who:** Administrator
**What:** Change product information
**How:**
- Find product to edit
- Update details as needed
- Save changes
- Changes appear in store

### 3. Manage Inventory
**Who:** Administrator
**What:** Update stock levels
**How:**
- View current inventory
- Update quantities for products
- System alerts for low stock

### 4. Process Orders
**Who:** Administrator
**What:** Handle customer orders
**How:**
- View pending orders
- Update status (paid, shipped, delivered)
- Add tracking information
- Notify customers

### 5. Moderate Reviews
**Who:** Administrator
**What:** Review customer feedback
**How:**
- View pending reviews
- Approve or reject reviews
- Ensure appropriate content

## Guest Use Cases

### 1. Browse as Guest
**Who:** Unregistered visitor
**What:** Look at products without account
**How:**
- Visit website
- Browse products
- Add items to temporary cart
- Prompted to register at checkout

### 2. Guest Checkout
**Who:** Unregistered visitor
**What:** Buy without creating account
**How:**
- Add items to cart
- Enter shipping and payment info
- Complete purchase
- Receive order confirmation

## System Use Cases

### 1. Send Confirmation
**What:** Notify customers of order
**How:**
- Detect completed order
- Send email confirmation
- Include order details

### 2. Update Inventory
**What:** Adjust stock after purchase
**How:**
- Detect paid order
- Reduce product quantities
- Alert if stock is low

### 3. Process Payment
**What:** Handle payment transaction
**How:**
- Validate payment info
- Connect with payment provider
- Confirm payment
- Update order status

### 4. Generate Reports
**What:** Create business reports
**How:**
- Collect sales data
- Format report
- Deliver to admin

## Quick Reference Table

| Action | Who | Result |
|--------|-----|---------|
| Create Account | New Customer | Active account |
| Log In | Customer | Authenticated access |
| Browse Products | Anyone | View product catalog |
| Search | Anyone | Find specific items |
| Add to Cart | Anyone | Items in cart |
| Checkout | Customer | Order placed |
| Track Order | Customer | Know order status |
| Add Product | Admin | Product in store |
| Process Orders | Admin | Orders fulfilled |
| Send Confirmation | System | Customer notified |
| Update Inventory | System | Stock levels adjusted |
