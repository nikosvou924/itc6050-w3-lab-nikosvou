SET search_path TO shop;

-- Q1: Monthly revenue trend
SELECT 
    date_trunc('month', order_date)::date AS month,
    COUNT(*) AS orders,
    SUM(total) AS revenue
FROM shop.orders
GROUP BY date_trunc('month', order_date)
ORDER BY month;

-- Q2: Top 10 products by revenue
SELECT 
    p.name AS product_name,
    SUM(oi.quantity) AS total_qty,
    SUM(oi.quantity * oi.unit_price_at_sale) AS revenue
FROM shop.order_item oi
JOIN shop.product p USING (product_id)
GROUP BY p.name
ORDER BY revenue DESC
LIMIT 10;

-- Q3: Average order value by status
SELECT
    status,
    COUNT(*) AS orders,
    ROUND(AVG(total)::numeric, 2) AS avg_total,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total)::numeric, 2) AS median_total
FROM shop.orders
GROUP BY status
ORDER BY status;

-- Q4: Dormant customers (no order in last 90 days)
SELECT 
    c.email,
    MAX(o.order_date) AS last_order_date,
    EXTRACT(DAY FROM NOW() - MAX(o.order_date)) AS days_dormant
FROM shop.customer c
JOIN shop.orders o USING (customer_id)
GROUP BY c.customer_id, c.email
HAVING MAX(o.order_date) < NOW() - INTERVAL '90 days'
ORDER BY days_dormant DESC;

-- Q5: Top 20 customers by lifetime spend with window functions

WITH customer_spend AS (
    SELECT
        c.email,
        SUM(total) AS lifetime_spend
    FROM shop.orders o
    JOIN shop.customer c USING (customer_id)
    GROUP BY c.customer_id, c.email
)
SELECT
    RANK() OVER (ORDER BY lifetime_spend DESC) AS rank,
    email,
    ROUND(lifetime_spend::numeric, 2) AS lifetime_spend,
    ROUND(
        (LAG(lifetime_spend) OVER (ORDER BY lifetime_spend DESC) - lifetime_spend)::numeric,
        2
    ) AS gap_to_previous
FROM customer_spend
ORDER BY lifetime_spend DESC
LIMIT 20;
