// =============================================================
// Power Query (M) — paste each block into Home → Transform Data
// → New Source → Blank Query → Advanced Editor.
// All connections use DirectQuery mode (MySql.Database with
// CreateNavigationProperties=false to keep the model clean).
// =============================================================

// ---- orders (fact) -----------------------------------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    orders = Source{[Schema = "ecommerce_rt", Item = "orders"]}[Data]
in
    orders

// ---- order_items (fact, line-level) -------------------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    order_items = Source{[Schema = "ecommerce_rt", Item = "order_items"]}[Data]
in
    order_items

// ---- products (dimension) -----------------------------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    products = Source{[Schema = "ecommerce_rt", Item = "products"]}[Data]
in
    products

// ---- sales_metrics (minute aggregates) ----------------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    sales_metrics = Source{[Schema = "ecommerce_rt", Item = "sales_metrics"]}[Data]
in
    sales_metrics

// ---- product_sales_metrics (minute per-product) -------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    product_sales_metrics = Source{[Schema = "ecommerce_rt", Item = "product_sales_metrics"]}[Data]
in
    product_sales_metrics

// ---- alerts -------------------------------------------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    alerts = Source{[Schema = "ecommerce_rt", Item = "alerts"]}[Data]
in
    alerts

// ---- kpi_thresholds (config dimension) ----------------------
let
    Source = MySQL.Database(
        "localhost:3306",
        "ecommerce_rt",
        [CreateNavigationProperties = false, ReturnSingleDatabase = true]
    ),
    kpi_thresholds = Source{[Schema = "ecommerce_rt", Item = "kpi_thresholds"]}[Data]
in
    kpi_thresholds

// ---- DateTable (Import, NOT DirectQuery) --------------------
// Use Modeling → New Table and paste this DAX instead (simpler):
//     DateTable = CALENDAR(DATE(YEAR(TODAY())-1,1,1), TODAY() + 30)
// then mark as date table on DateTable[Date].
