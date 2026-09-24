DATABASE_SCHEMA = """
PostgreSQL database containing the Olist Brazilian E-commerce dataset.

TABLE customers
- customer_id: primary key
- customer_unique_id: identifier representing the same real customer across orders
- customer_zip_code_prefix
- customer_city
- customer_state

TABLE orders
- order_id: primary key
- customer_id: foreign key -> customers.customer_id
- order_status
- order_purchase_timestamp
- order_approved_at
- order_delivered_carrier_date
- order_delivered_customer_date
- order_estimated_delivery_date

TABLE order_items
- order_id: foreign key -> orders.order_id
- order_item_id
- product_id: foreign key -> products.product_id
- seller_id: foreign key -> sellers.seller_id
- shipping_limit_date
- price
- freight_value
- primary key: (order_id, order_item_id)

TABLE order_payments
- order_id: foreign key -> orders.order_id
- payment_sequential
- payment_type
- payment_installments
- payment_value
- primary key: (order_id, payment_sequential)

TABLE order_reviews
- review_id
- order_id: foreign key -> orders.order_id
- review_score
- review_comment_title
- review_comment_message
- review_creation_date
- review_answer_timestamp
- primary key: (review_id, order_id)

TABLE products
- product_id: primary key
- product_category_name
- product_name_length
- product_description_length
- product_photos_qty
- product_weight_g
- product_length_cm
- product_height_cm
- product_width_cm

TABLE sellers
- seller_id: primary key
- seller_zip_code_prefix
- seller_city
- seller_state

TABLE category_translation
- product_category_name: primary key
- product_category_name_english

TABLE geolocation
- geolocation_zip_code_prefix
- geolocation_lat
- geolocation_lng
- geolocation_city
- geolocation_state

Important:
- geolocation has duplicate rows and does not have a primary key.
- product_category_name is not guaranteed to exist in category_translation.
"""


BUSINESS_RULES = """
Business metric definitions:

1. Product Revenue
- Use order_items.price.
- Include only orders where order_status = 'delivered'.
- Freight is not included in product revenue.

2. Freight Revenue
- Use order_items.freight_value.
- Include only delivered orders.

3. Gross Item Value
- Defined as price + freight_value.
- Include only delivered orders.

4. Average Order Value (AOV)
- Include only delivered orders.
- First calculate SUM(order_items.price) for each order.
- Then calculate the average of those order-level revenues.
- Do NOT calculate AVG(order_items.price).

5. Delivery Delay
- Evaluate delivered orders with a non-null order_delivered_customer_date.
- An order is delayed when:
  order_delivered_customer_date > order_estimated_delivery_date.

6. Review Score
- review_score ranges from 1 to 5.
- Scores <= 2 are treated as negative reviews.
- Scores >= 4 are treated as positive reviews.

7. Product Category
- Join products to category_translation using LEFT JOIN.
- Some product categories do not have an English translation.
- Preserve those categories instead of dropping them.

General SQL rules:
- PostgreSQL syntax must be used.
- Prefer explicit JOIN conditions.
- Avoid SELECT * when a smaller result is sufficient.
- Do not modify data.
"""