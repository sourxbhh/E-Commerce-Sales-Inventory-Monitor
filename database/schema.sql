-- ============================================================
-- E-Commerce Real-Time Monitor: Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce_rt;
USE ecommerce_rt;

-- ------------------------------------------------------------
-- products
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id         INT PRIMARY KEY,
    name               VARCHAR(200) NOT NULL,
    category           VARCHAR(80)  NOT NULL,
    price              DECIMAL(10,2) NOT NULL,
    stock_quantity     INT NOT NULL,
    reorder_threshold  INT NOT NULL,
    popularity_weight  DECIMAL(5,2) DEFAULT 1.00,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_stock (stock_quantity, reorder_threshold)
);

-- ------------------------------------------------------------
-- orders
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id         VARCHAR(64) PRIMARY KEY,
    customer_id      VARCHAR(64) NOT NULL,
    order_timestamp  TIMESTAMP(3) NOT NULL,
    total_amount     DECIMAL(12,2) NOT NULL,
    item_count       INT NOT NULL,
    status           VARCHAR(20) NOT NULL DEFAULT 'CREATED',
    inserted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ts (order_timestamp),
    INDEX idx_customer (customer_id)
);

-- ------------------------------------------------------------
-- order_items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id        VARCHAR(64) NOT NULL,
    product_id      INT NOT NULL,
    quantity        INT NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    line_total      DECIMAL(12,2) AS (quantity * unit_price) STORED,
    INDEX idx_order (order_id),
    INDEX idx_product (product_id)
);

-- ------------------------------------------------------------
-- inventory_log
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_log (
    log_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id       INT NOT NULL,
    change_type      VARCHAR(20) NOT NULL,
    quantity_change  INT NOT NULL,
    stock_after      INT NOT NULL,
    event_timestamp  TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    INDEX idx_product_ts (product_id, event_timestamp)
);

-- ------------------------------------------------------------
-- sales_metrics (minute-level aggregates from Spark)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales_metrics (
    metric_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    window_start     TIMESTAMP NOT NULL,
    window_end       TIMESTAMP NOT NULL,
    revenue          DECIMAL(14,2) NOT NULL,
    order_count      INT NOT NULL,
    item_count       INT NOT NULL,
    avg_order_value  DECIMAL(10,2) NOT NULL,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_window (window_start, window_end),
    INDEX idx_window (window_start)
);

-- ------------------------------------------------------------
-- product_sales_metrics (per-product minute aggregates)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_sales_metrics (
    metric_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
    window_start    TIMESTAMP NOT NULL,
    window_end      TIMESTAMP NOT NULL,
    product_id      INT NOT NULL,
    units_sold      INT NOT NULL,
    revenue         DECIMAL(12,2) NOT NULL,
    UNIQUE KEY uq_window_prod (window_start, window_end, product_id),
    INDEX idx_window_prod (window_start, product_id)
);

-- ------------------------------------------------------------
-- alerts
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    alert_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_type       VARCHAR(40) NOT NULL,
    severity         VARCHAR(20) NOT NULL,
    entity_type      VARCHAR(40),
    entity_id        VARCHAR(64),
    message          VARCHAR(500) NOT NULL,
    detected_value   DECIMAL(14,4),
    expected_low     DECIMAL(14,4),
    expected_high    DECIMAL(14,4),
    detected_at      TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    resolved         TINYINT(1) DEFAULT 0,
    INDEX idx_type_ts (alert_type, detected_at),
    INDEX idx_severity (severity, detected_at)
);

-- ------------------------------------------------------------
-- kpi_thresholds (dynamic alert configuration)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kpi_thresholds (
    threshold_id         INT AUTO_INCREMENT PRIMARY KEY,
    metric_name          VARCHAR(80) NOT NULL UNIQUE,
    description          VARCHAR(300),
    warning_threshold    DECIMAL(14,4),
    critical_threshold   DECIMAL(14,4),
    comparison_operator  VARCHAR(5) NOT NULL,
    window_minutes       INT NOT NULL DEFAULT 5,
    enabled              TINYINT(1) DEFAULT 1,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Seed KPI thresholds
-- ------------------------------------------------------------
INSERT INTO kpi_thresholds
    (metric_name, description, warning_threshold, critical_threshold, comparison_operator, window_minutes)
VALUES
    ('revenue_per_5min',   'Total revenue in last 5 minutes',   200.00, 50.00,  '<', 5),
    ('orders_per_5min',    'Order count in last 5 minutes',     10,     2,      '<', 5),
    ('low_stock_count',    'Products at/below reorder point',   5,      15,     '>', 1),
    ('avg_order_value',    'Rolling average order value (5m)',  30.00,  10.00,  '<', 5),
    ('revenue_drop_pct',   'Revenue % drop vs prior 5m window', 30.00,  60.00,  '>', 5)
ON DUPLICATE KEY UPDATE description = VALUES(description);
