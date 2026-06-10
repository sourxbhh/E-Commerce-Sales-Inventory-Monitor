// Power Query (M) for the Olist report. Pulls the dbt marts from DuckDB over
// ODBC in Import mode. Set the DbPath parameter to your warehouse/olist.duckdb.
//
// Power BI Desktop: Home > Transform data > New Parameter `DbPath` (Text),
// then paste each query below as a new blank query.

// --- Parameter ---
// DbPath = "D:\Projects\DataAnalyst\E-Commerce\warehouse\olist.duckdb"

let
    ConnStr = "Driver={DuckDB Driver};Database=" & DbPath & ";access_mode=READ_ONLY",
    Source  = Odbc.DataSource(ConnStr, [HierarchicalNavigation = true])
in
    Source

// --- fct_orders ---
// let
//     Source = #"DuckDB",
//     fct = Source{[Schema = "main_marts", Item = "fct_orders"]}[Data]
// in
//     fct

// --- dim_customers ---
// let
//     Source = #"DuckDB",
//     dim = Source{[Schema = "main_marts", Item = "dim_customers"]}[Data]
// in
//     dim

// --- dim_products ---
// let
//     Source = #"DuckDB",
//     dim = Source{[Schema = "main_marts", Item = "dim_products"]}[Data]
// in
//     dim
