# Power BI Dashboard — Build Guide (Phase 7)

Walk through this once, top to bottom, to reproduce the dashboard.
All visuals use **DirectQuery** against MySQL on `localhost:3306`.

## 0. Initial connection

1. Open Power BI Desktop → **File → Import → Power BI template**
   and pick `dashboard/connection.pbids` (or use **Get Data → MySQL**).
2. Server `localhost:3306`, database `ecommerce_rt`, connectivity
   mode **DirectQuery**. Credentials: `ecom_user` / `ecom_pass`.
3. Select these tables and click **Load**:
   `orders`, `order_items`, `products`, `sales_metrics`,
   `product_sales_metrics`, `alerts`, `kpi_thresholds`.

If you prefer M, copy the blocks from `power_query.m` into new blank
queries instead.

## 1. Apply the theme

View → Themes → **Browse for themes** → select `dashboard/theme.json`.
This sets the palette, spacing, card styles, and borders referenced
below.

## 2. Data model

Model view — create these relationships (Cross filter = Single,
direction shown):

| From | To | Cardinality | Direction |
|---|---|---|---|
| `orders[order_id]` | `order_items[order_id]` | 1 — * | orders → items |
| `products[product_id]` | `order_items[product_id]` | 1 — * | products → items |
| `products[product_id]` | `product_sales_metrics[product_id]` | 1 — * | products → metrics |

Mark `orders[order_timestamp]` and `sales_metrics[window_start]` as
date-time. Hide `order_items[order_item_id]` and all integer PKs.

Create a DAX calendar so time intelligence works:

```DAX
DateTable =
    ADDCOLUMNS (
        CALENDAR ( DATE ( YEAR ( TODAY () ) - 1, 1, 1 ), TODAY () + 30 ),
        "Year",     YEAR ( [Date] ),
        "Month",    FORMAT ( [Date], "MMM yyyy" ),
        "MonthNum", YEAR ( [Date] ) * 100 + MONTH ( [Date] ),
        "Day",      DAY ( [Date] ),
        "Weekday",  FORMAT ( [Date], "ddd" )
    )
```

Modeling → Mark as date table → `DateTable[Date]`.
Relate `DateTable[Date]` → `orders[order_timestamp]` (cast to date in
the PK column via a calculated column if needed).

## 3. Measures

Paste the full `measures.dax` file into the model (Modeling → New
Measure, one measure at a time, or use **Tabular Editor** for a bulk
paste). Organise into the display folders suggested inside the file.

## 4. Pages

Each page is 1280 × 720 with the background from the theme. Use a
common page header strip (title + auto-refresh time) 1280 × 60 at
y=0, and a visual grid below.

---

### Page 1 — Live Overview

Purpose: one-glance operational status. Refresh every minute.

**Row 1 — KPI cards (4 across, y=80, h=140):**

| Card | Measure | Conditional formatting |
|---|---|---|
| Revenue Today | `Total Revenue Today` | Font colour by `Revenue Trend Color` |
| Orders Today | `Orders Today` | — |
| Avg Order Value | `Average Order Value Today` | — |
| Active Alerts | `Active Alerts` | Background red if `Critical Alerts > 0` |

Add the **Revenue Trend Arrow** measure as a secondary label under the
Revenue Today card.

**Row 2 — Revenue/minute line chart (y=240, w=840, h=360):**

- Visual: Line chart
- X: `sales_metrics[window_start]` (continuous)
- Y: `sum(sales_metrics[revenue])`
- Filter: `window_start >= NOW() - (2/24)` (last 2 hours)
- Analytics pane: add **Average line** and **Min/Max lines**
- Tooltips: revenue, order_count, avg_order_value

**Row 2 — Alerts feed (y=240, x=860, w=400, h=360):**

- Visual: Table
- Columns: `detected_at`, `severity`, `alert_type`, `message`
- Filter: `resolved = 0`
- Sort: `detected_at` desc, top 15
- Conditional formatting: background colour by `Severity Color`

**Row 3 — KPI gauge strip (y=620, h=90):**
- Four small gauges or cards driven by the KPI_VIOLATION feed so
  operators see which SLOs are currently breaching.

**Page auto-refresh:** Format → Page refresh → On → Change detection
off → Refresh period **1 minute** (DirectQuery requirement).

---

### Page 2 — Top Sellers

**Slicers** (top strip): date range, category, popularity tier.

**Visuals:**

1. **Top 10 products (bar chart, horizontal)** — product name × `Units Sold`, sort desc, top N = 10.
2. **Revenue by category (treemap)** — `products[category]` × `Line Revenue`.
3. **Category share over time (stacked area chart)** — x=`order_timestamp` (hourly bins), y=`Line Revenue`, legend=`category`.
4. **Product detail table** — product_id, name, category, price, Units Sold, Line Revenue, stock_quantity, `Stock Health Icon`. Row background via `Stock Row Color`.

---

### Page 3 — Inventory Health

**Visuals:**

1. **Low-stock matrix** — rows = category → product, values = `stock_quantity`, `reorder_threshold`, `Stock Health Icon`. Conditional formatting background on `stock_quantity` with colour scale (red = 0, yellow at threshold, green above 2× threshold).
2. **Reorder suggestion table** — filter `stock_quantity <= reorder_threshold`, columns: product, current stock, threshold, suggested order qty = `reorder_threshold * 3 - stock_quantity`.
3. **Stock level distribution (histogram)** — group products into bins (0, 1-10, 10-25% of threshold, etc.).
4. **Top depletion velocity (bar chart)** — x=product, y=`Units Sold` over last hour (filter product_sales_metrics to last 60 min).

---

### Page 4 — Alerts & Anomalies

**Visuals:**

1. **Alert count by hour (column chart)** — x=hour, y=COUNT(alert_id), legend=`alert_type`.
2. **Anomaly overlay (line + scatter)** — line = `sales_metrics[revenue]` per minute; scatter = alert points (filter `alerts[alert_type] = "REVENUE_SPIKE"`) on the same axis. Anomalies appear as red dots on the revenue line.
3. **KPI violation heatmap** — matrix, rows=`kpi_thresholds[metric_name]`, columns=hour, values=count of `KPI_VIOLATION` alerts.
4. **Alert log table** — all columns from `alerts`, sorted `detected_at` desc, conditional background on severity, filter slicer for `alert_type`.

---

## 5. Page refresh configuration

Repeat for every page that shows live data (Pages 1 and 4 at minimum):

1. Click an empty area of the page.
2. Format pane → **Page information** → **Page refresh = On**.
3. Refresh type = **Auto page refresh**.
4. Set period to `1 minute` (or 30 sec if on Premium capacity).

Power BI Desktop will warn if the admin hasn’t enabled APR — in that
case, publish and set refresh in the service.

## 6. Publishing

- **File → Save As** → `dashboard/EcomRealtimeMonitor.pbix`.
- **File → Publish** → pick a workspace.
- In the service, configure a Gateway so DirectQuery can reach your
  local MySQL (or migrate MySQL to cloud first — see
  `docs/CLOUD_DEPLOYMENT.md`).

## 7. Demo tips

- Page 1 is the shareable "screen on the wall" view.
- Page 4 is where you click through during a burst demo to show both
  the revenue spike dot and the matching alert row appearing.
- Page 3 works best after running `scripts/demo_controller.py drain`
  to deliberately deplete a few SKUs.
