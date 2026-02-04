# Products App

The Products app is a core component of the e-commerce platform, providing comprehensive management for products, categories, inventory, orders, payments, and reviews.

## Overview

This app handles all product-related operations including:
- Product catalog management
- Category hierarchy
- Inventory tracking
- Order processing
- Payment handling
- Customer reviews

## Features

### Product Management
- Full CRUD operations for products
- Product categorization with hierarchical categories
- Product descriptions and pricing
- Active/inactive product states

### Category System
- Hierarchical category structure (parent-child relationships)
- Category trees for navigation
- Nested category display

### Inventory Management
- Stock level tracking
- Reserved quantity management
- Available quantity calculation

### Order Processing
- Complete order lifecycle management
- Order items tracking
- Shipping address association
- Order status updates

### Payment Handling
- Multiple payment providers support
- Transaction reference tracking
- Payment status monitoring

### Reviews System
- Customer review submission
- Product rating system (1-5 stars)
- Review moderation capabilities

## Models

### Product
- `id`: UUID primary key
- `name`: Product name (indexed)
- `description`: Detailed product description
- `slug`: Unique URL-friendly identifier (indexed)
- `price`: Decimal price value
- `currency`: Currency code (default: CFA)
- `categories`: Many-to-many relationship with categories
- `is_active`: Boolean flag for product availability

### Category
- `id`: UUID primary key
- `name`: Category name (indexed)
- `parent`: Self-referencing foreign key for hierarchy

### Inventory
- `id`: UUID primary key
- `product`: One-to-one relationship with Product
- `quantity`: Total available quantity
- `reserved_quantity`: Quantity reserved for pending orders
- `available_quantity`: Calculated property (quantity - reserved_quantity)

### Order
- `id`: UUID primary key
- `customer`: Foreign key to CustomUser
- `shipping_address`: Foreign key to Address
- `status`: Order status (pending, paid, shipped, delivered, cancelled)
- `total_price`: Total order amount
- `currency`: Currency code

### Payment
- `id`: UUID primary key
- `order`: One-to-one relationship with Order
- `provider`: Payment service provider
- `amount`: Payment amount
- `status`: Payment status (pending, completed, failed, refunded)
- `transaction_reference`: External transaction ID

### Review
- `id`: UUID primary key
- `product`: Foreign key to Product
- `customer`: Foreign key to CustomUser
- `rating`: Integer rating (1-5)
- `title`: Optional review title
- `content`: Review content
- `comment`: Optional additional comment

## API Endpoints

### Categories
- `GET /api/v1/products/categories/` - List all categories
- `POST /api/v1/products/categories/` - Create a new category
- `GET /api/v1/products/categories/{id}/` - Retrieve a specific category
- `PUT /api/v1/products/categories/{id}/` - Update a category
- `DELETE /api/v1/products/categories/{id}/` - Delete a category
- `GET /api/v1/products/categories/tree/` - Get category tree structure

### Products
- `GET /api/v1/products/` - List all products with filtering options
- `POST /api/v1/products/` - Create a new product
- `GET /api/v1/products/{id}/` - Retrieve a specific product
- `PUT /api/v1/products/{id}/` - Update a product
- `DELETE /api/v1/products/{id}/` - Delete a product
- `GET /api/v1/products/search/` - Search products by name or description

### Addresses
- `GET /api/v1/products/addresses/` - List user's addresses
- `POST /api/v1/products/addresses/` - Create a new address
- `GET /api/v1/products/addresses/{id}/` - Retrieve a specific address
- `PUT /api/v1/products/addresses/{id}/` - Update an address
- `DELETE /api/v1/products/addresses/{id}/` - Delete an address

### Inventory
- `GET /api/v1/products/inventory/` - List all inventory items
- `POST /api/v1/products/inventory/` - Create a new inventory record
- `GET /api/v1/products/inventory/{id}/` - Retrieve specific inventory
- `PUT /api/v1/products/inventory/{id}/` - Update inventory
- `DELETE /api/v1/products/inventory/{id}/` - Delete inventory

### Orders
- `GET /api/v1/products/orders/` - List user's orders
- `POST /api/v1/products/orders/` - Create a new order
- `GET /api/v1/products/orders/{id}/` - Retrieve a specific order
- `PUT /api/v1/products/orders/{id}/` - Update an order
- `DELETE /api/v1/products/orders/{id}/` - Cancel an order

### Payments
- `GET /api/v1/products/payments/` - List all payments
- `POST /api/v1/products/payments/` - Create a new payment
- `GET /api/v1/products/payments/{id}/` - Retrieve a specific payment
- `PUT /api/v1/products/payments/{id}/` - Update a payment
- `DELETE /api/v1/products/payments/{id}/` - Delete a payment

### Reviews
- `GET /api/v1/products/reviews/` - List all reviews with filtering
- `POST /api/v1/products/reviews/` - Create a new review
- `GET /api/v1/products/reviews/{id}/` - Retrieve a specific review
- `PUT /api/v1/products/reviews/{id}/` - Update a review
- `DELETE /api/v1/products/reviews/{id}/` - Delete a review

## Filtering and Search Options

### Product Filtering
- `category`: Filter by category ID
- `min_price` / `max_price`: Price range filtering
- `search`: Search in name and description fields

### General Filtering
- `ordering`: Sort by fields like `created_at`, `name`, `price`
- `search`: Search in designated fields for each model

## Authentication

Most endpoints require authentication using JWT tokens. Public endpoints include product and category listings.

## Dependencies

- Django REST Framework
- django-filters
- drf-yasg (for API documentation)

