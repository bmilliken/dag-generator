# Column-Level Lineage Test Case

This finance project demonstrates the difference between **table-level** and **column-level** lineage tracking.

## Project Structure

### Source Tables (4):
- `src.users` - User information
- `src.orders` - Order records  
- `src.products` - Product catalog
- `src.order_items` - Line items per order

### Staging Tables (2):
- `stg.clean_users` - Cleaned user data with generated fields
- `stg.enriched_orders` - Orders with calculated aggregates

### Mart Tables (1):
- `mart.user_summary` - Final business summary

## Key Lineage Insights

### Table-Level vs Column-Level Dependencies

If you only tracked **table-level** lineage, you'd see:
```
mart.user_summary depends on:
  └── stg.clean_users depends on:
      └── src.users
  └── stg.enriched_orders depends on:
      └── src.orders
      └── src.order_items
  └── src.products (direct)
```

This would suggest `mart.user_summary` depends on ALL columns in ALL these tables.

### But Column-Level Lineage Shows:

1. **`user_id`** → only depends on `src.users.user_id`
2. **`username`** → only depends on `src.users.username`  
3. **`product_category`** → only depends on `src.products.category`
4. **`email_domain`** → depends on `stg.clean_users.email_domain` → `src.users.email`
5. **`avg_order_value`** → depends on `stg.enriched_orders.item_count` + `stg.enriched_orders.order_revenue` → `src.order_items.quantity` + `src.order_items.unit_price`

### Critical Insight:
Even though `mart.user_summary` is connected to the order processing pipeline, the `user_id` and `username` columns have **ZERO dependency** on:
- `src.orders.total_amount`
- `src.order_items.unit_price` 
- `src.products.price`
- `src.products.supplier_id`
- etc.

This is the power of column-level lineage - it shows exactly which upstream changes affect which downstream columns, not just which tables are connected.

## Test Scenarios

1. **Click on `mart.user_summary`** - Should only highlight the specific columns it actually depends on
2. **Click on `src.products.price`** - Should show it has NO impact on the mart table
3. **Click on `src.users.email`** - Should trace through the transformation to `email_domain`
4. **Click on `src.order_items.quantity`** - Should show it only affects the `avg_order_value` field
