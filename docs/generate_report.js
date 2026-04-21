/**
 * Generates docs/Project_Complete_Guide.docx — an interview-ready walkthrough of the
 * Real-Time E-Commerce Sales & Inventory Monitor. Child-friendly analogies up top,
 * detailed component breakdowns + code walkthroughs + Q&A below.
 *
 *     node docs/generate_report.js
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  TabStopType, TabStopPosition, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TableOfContents, ExternalHyperlink,
} = require("docx");

// -------------------------------------------------------------------------
// small helpers
// -------------------------------------------------------------------------

const FONT = "Calibri";
const MONO = "Consolas";

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, bold: true })],
});
const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, bold: true })],
});
const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, bold: true })],
});

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 120 },
  children: [new TextRun({ text, ...opts })],
});

const Pmulti = (runs) => new Paragraph({
  spacing: { after: 120 },
  children: runs,
});

const Bullet = (text, level = 0) => new Paragraph({
  numbering: { reference: "bullets", level },
  spacing: { after: 60 },
  children: [new TextRun({ text })],
});

const BulletRuns = (runs, level = 0) => new Paragraph({
  numbering: { reference: "bullets", level },
  spacing: { after: 60 },
  children: runs,
});

const Numbered = (text, level = 0) => new Paragraph({
  numbering: { reference: "numbers", level },
  spacing: { after: 60 },
  children: [new TextRun({ text })],
});

const Note = (text) => new Paragraph({
  spacing: { before: 60, after: 120 },
  indent: { left: 360 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "2E75B6", space: 8 } },
  children: [new TextRun({ text, italics: true, color: "444444" })],
});

// monospace code block — one TextRun per line, joined by newline break
const Code = (code) => {
  const lines = code.split("\n");
  const runs = [];
  lines.forEach((line, i) => {
    if (i > 0) runs.push(new TextRun({ break: 1 }));
    runs.push(new TextRun({ text: line, font: MONO, size: 18 }));
  });
  return new Paragraph({
    spacing: { before: 80, after: 160 },
    shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" },
    border: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
      left:   { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
      right:  { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" },
    },
    children: runs,
  });
};

const Spacer = () => new Paragraph({ children: [new TextRun(" ")] });

// Simple 2-col table for quick reference grids
const thinBorder = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const tableBorders = {
  top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder,
  insideHorizontal: thinBorder, insideVertical: thinBorder,
};

const TwoColTable = (rows, leftHeader = "Key", rightHeader = "Value", widths = [3120, 6240]) => {
  const total = widths[0] + widths[1];
  const headerCell = (text, w) => new TableCell({
    borders: tableBorders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: "2E75B6", type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: "FFFFFF" })],
    })],
  });
  const bodyCell = (text, w, mono = false) => new TableCell({
    borders: tableBorders,
    width: { size: w, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun(mono ? { text, font: MONO, size: 18 } : { text })],
    })],
  });
  const tRows = [
    new TableRow({ tableHeader: true, children: [
      headerCell(leftHeader, widths[0]),
      headerCell(rightHeader, widths[1]),
    ] }),
  ];
  for (const [l, r] of rows) {
    tRows.push(new TableRow({ children: [
      bodyCell(l, widths[0], true),
      bodyCell(r, widths[1], false),
    ] }));
  }
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: tRows,
  });
};

// -------------------------------------------------------------------------
// content
// -------------------------------------------------------------------------

const children = [];

// ---------- TITLE ----------
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 2400, after: 240 },
    children: [new TextRun({
      text: "Real-Time E-Commerce Sales & Inventory Monitor",
      bold: true, size: 48, color: "1F3864",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({
      text: "The Complete Interview-Prep Guide",
      size: 32, color: "2E75B6",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 2400 },
    children: [new TextRun({
      text: "Explained like you're five, then detailed like you're defending it.",
      italics: true, size: 24, color: "666666",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "FakeStoreAPI  \u2192  FastAPI  \u2192  Kafka  \u2192  Spark Structured Streaming  \u2192  MySQL  \u2192  Power BI",
      size: 20, color: "444444",
    })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---------- TABLE OF CONTENTS ----------
children.push(
  H1("Table of Contents"),
  new TableOfContents("Table of Contents", {
    hyperlink: true,
    headingStyleRange: "1-3",
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 1. ELI5 — THE BIG PICTURE
// ===========================================================================
children.push(
  H1("1. The Big Picture (Explain Like I'm Five)"),
  P("Imagine a pizza shop. People place orders, the kitchen cooks them, a dashboard on the wall shows how many pizzas were sold in the last minute, and a manager yells when cheese is running low. This whole project is that pizza shop — but for an online store, and instead of pizzas we're selling real products (headphones, jewelry, t-shirts) pulled from a real website called FakeStoreAPI."),
  H2("1.1 The Characters"),
  BulletRuns([
    new TextRun({ text: "FakeStoreAPI ", bold: true }),
    new TextRun("— the \"menu supplier\". A free public website that hands us 20 real products with real prices, categories, and ratings. No login required."),
  ]),
  BulletRuns([
    new TextRun({ text: "FastAPI (the order taker) ", bold: true }),
    new TextRun("— a tiny Python web server that pretends to be a checkout system. Every 2–5 seconds it invents a new order and shouts it into a loudspeaker."),
  ]),
  BulletRuns([
    new TextRun({ text: "Kafka (the loudspeaker / conveyor belt) ", bold: true }),
    new TextRun("— a giant message bus. When the order taker shouts \"Order #123!\", anyone wearing headphones tuned to that channel hears it — even if they show up late, because Kafka remembers."),
  ]),
  BulletRuns([
    new TextRun({ text: "Spark Structured Streaming (the accountant) ", bold: true }),
    new TextRun("— listens to the loudspeaker, counts every order that came in during each minute, multiplies price × quantity, and writes the totals in a ledger."),
  ]),
  BulletRuns([
    new TextRun({ text: "MySQL (the ledger) ", bold: true }),
    new TextRun("— a database where all the numbers live: every order, every minute's revenue, every low-stock warning."),
  ]),
  BulletRuns([
    new TextRun({ text: "Anomaly Detector (the suspicious auditor) ", bold: true }),
    new TextRun("— reads the ledger every minute and says \"hey, this minute's revenue is 4× higher than usual — something's weird\"."),
  ]),
  BulletRuns([
    new TextRun({ text: "KPI Evaluator (the rule-book enforcer) ", bold: true }),
    new TextRun("— checks the numbers against business rules (\"revenue must be > $100/5min\") and raises an alarm if they break."),
  ]),
  BulletRuns([
    new TextRun({ text: "Power BI (the big TV on the wall) ", bold: true }),
    new TextRun("— a dashboard that reads the ledger and shows pretty charts, updating every minute."),
  ]),
  H2("1.2 A Day in the Life of One Order"),
  Numbered("FastAPI wakes up, rolls some dice, and builds an order: \"Customer C-0042 bought 2 headphones + 1 ring for $157.98.\""),
  Numbered("It writes that order into Kafka's orders topic."),
  Numbered("Spark is listening on that topic. It grabs the order, puts it in a 1-minute bucket, and at the end of the minute writes the bucket's totals into MySQL."),
  Numbered("Spark also subtracts 2 from headphones' stock and 1 from ring's stock. If any stock drops below its threshold, it writes a LOW_STOCK alert."),
  Numbered("One minute later, the anomaly detector reads MySQL, sees revenue shot up 5×, and writes a REVENUE_SPIKE alert."),
  Numbered("Power BI, refreshing every 60 seconds, pulls the new numbers and the new alerts, updating the dashboard in front of the analyst's eyes."),
  Note("That's the entire pipeline: one real order flowing from \"invented\" to \"painted on a chart\" in under 90 seconds, with watermarks, windows, and idempotent upserts happening under the hood."),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 2. ARCHITECTURE
// ===========================================================================
children.push(
  H1("2. Architecture"),
  H2("2.1 The Flow, Drawn in Words"),
  Code(
    "  fakestoreapi.com   (real products)\n" +
    "        |\n" +
    "        v\n" +
    "  scripts/fakestore_sync.py   --->   MySQL.products\n" +
    "        |\n" +
    "        v\n" +
    "  api/main.py (FastAPI)  ---- WebSocket ---->  browsers / notebooks\n" +
    "        |\n" +
    "        v\n" +
    "  Kafka topic: orders\n" +
    "        |\n" +
    "        v\n" +
    "  streaming/stream_processor.py (Spark)\n" +
    "        |-- writes orders + order_items\n" +
    "        |-- writes 1-min sales_metrics (revenue, order_count)\n" +
    "        |-- writes 1-min product_sales_metrics\n" +
    "        |-- decrements products.stock_quantity\n" +
    "        |-- emits LOW_STOCK alerts\n" +
    "        v\n" +
    "  MySQL   <---   anomaly/detector.py  (REVENUE_SPIKE alerts)\n" +
    "  MySQL   <---   kpi/evaluator.py     (KPI_VIOLATION alerts)\n" +
    "        |\n" +
    "        v\n" +
    "  Power BI Desktop (DirectQuery, 1-min refresh)"
  ),
  H2("2.2 Who Does What"),
  TwoColTable([
    ["FakeStoreAPI", "External free HTTP API. Supplies 20 real products + 7 historical carts (for basket-size mining)."],
    ["fakestore_sync.py", "One-shot Python script run on boot. Pulls the catalog, synthesizes stock + popularity, upserts into products."],
    ["api/main.py", "FastAPI uvicorn process. Hosts the order generator, the Kafka producer, the WebSocket broadcaster, and /trigger/* HTTP endpoints."],
    ["api/order_engine.py", "Builds orders: picks products weighted by popularity, samples basket size from real /carts distributions."],
    ["Kafka + Zookeeper", "Docker containers. Topics: orders, inventory-updates. Durable, replayable, multi-consumer."],
    ["stream_processor.py", "Spark Structured Streaming job. Reads Kafka, parses JSON, watermarks at 10 min, 1-min tumbling windows, writes five MySQL sinks in one foreachBatch."],
    ["anomaly/detector.py", "Polls sales_metrics every 60s. z-score fallback for < 15 rows, Isolation Forest afterwards. Emits REVENUE_SPIKE with 30-min dedupe."],
    ["kpi/evaluator.py", "Polls kpi_thresholds (config-as-data). Computes each metric against warn/critical and writes KPI_VIOLATION alerts."],
    ["MySQL 8", "Source of truth. 8 tables: products, orders, order_items, sales_metrics, product_sales_metrics, inventory_log, alerts, kpi_thresholds."],
    ["Power BI", "DirectQuery, 4 pages, 25+ DAX measures, 1-minute page auto-refresh."],
  ], "Component", "Responsibility", [2600, 6760]),
  H2("2.3 Why Each Piece Exists"),
  BulletRuns([
    new TextRun({ text: "Why FakeStoreAPI? ", bold: true }),
    new TextRun("Free, no-auth, real product identity and prices. More credible than pure Faker. Basket distributions come from real carts, so generated baskets are empirically shaped."),
  ]),
  BulletRuns([
    new TextRun({ text: "Why FastAPI at the edge? ", bold: true }),
    new TextRun("One process owns the generator + Kafka producer + WebSocket fan-out + HTTP triggers. Swagger UI documents itself. A dashboard in a browser can tap the same stream without touching Kafka."),
  ]),
  BulletRuns([
    new TextRun({ text: "Why Kafka (not a queue or just sockets)? ", bold: true }),
    new TextRun("Durable + replayable + multi-consumer. Spark can crash and resume. A second consumer can be added without disturbing the first."),
  ]),
  BulletRuns([
    new TextRun({ text: "Why Spark Structured Streaming? ", bold: true }),
    new TextRun("Exactly-once per micro-batch, native watermarking for late events, atomic multi-sink writes via foreachBatch."),
  ]),
  BulletRuns([
    new TextRun({ text: "Why MySQL (not a warehouse)? ", bold: true }),
    new TextRun("Good enough for minute-level aggregates at demo scale, plays beautifully with Power BI DirectQuery, cheap to run locally. Cloud migration doc shows the swap to BigQuery."),
  ]),
  BulletRuns([
    new TextRun({ text: "Why two anomaly strategies? ", bold: true }),
    new TextRun("Cold-start: Isolation Forest needs history. z-score fills the gap for the first ~15 minutes and then hands off."),
  ]),
  BulletRuns([
    new TextRun({ text: "Why config-as-data for KPIs? ", bold: true }),
    new TextRun("SLO tuning shouldn't require a code deploy. Edit a row in kpi_thresholds — next loop sees it."),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 3. COMPONENT DEEP DIVES
// ===========================================================================
children.push(H1("3. Component Deep Dives"));

// 3.1 FakeStoreAPI
children.push(
  H2("3.1 FakeStoreAPI — the Real Menu"),
  P("FakeStoreAPI is a free public REST API at fakestoreapi.com with 20 real products across 4 categories: electronics, jewelery, men's clothing, women's clothing. It also exposes /carts — 7 historical shopping carts with real basket shapes."),
  H3("What it gives us"),
  TwoColTable([
    ["id", "Product primary key"],
    ["title", "Real product name"],
    ["price", "Real USD price"],
    ["category", "One of 4 categories"],
    ["rating.rate", "0–5 star average"],
    ["rating.count", "Number of reviews (used to weight popularity)"],
  ], "Field", "Meaning", [2200, 7160]),
  H3("What we synthesize (FakeStoreAPI doesn't expose these)"),
  Code(
    "stock_quantity   = min(int(80 + sqrt(rating.count) * 12), 600)\n" +
    "reorder_threshold = max(int(stock_quantity * 0.20), 10)\n" +
    "popularity_weight = min(1.0 + log10(rating.count + 1), 4.5)\n\n" +
    "# popular items get stocked heavier AND picked more often."
  ),
  H3("Why this shape?"),
  Bullet("Popular products (high rating.count) should both sell more and have more stock — mirrors real retail."),
  Bullet("Logarithmic weight prevents the top-rated item from dominating every order."),
  Bullet("Floor of 10 on the reorder threshold keeps the LOW_STOCK demo achievable even for niche items."),
);

// 3.2 FastAPI
children.push(
  H2("3.2 FastAPI — the Live Edge"),
  P("A single uvicorn process that fuses five responsibilities: order generator, Kafka producer, WebSocket fan-out, HTTP trigger surface, and self-documenting Swagger. This is the only component that external consumers can reach — everything downstream is internal."),
  H3("Endpoints"),
  TwoColTable([
    ["GET /health", "Liveness + orders_sent counter"],
    ["GET /stats", "Rate, uptime, subscriber count, drain state"],
    ["GET /products", "Hydrated catalog from MySQL"],
    ["GET /products/{id}", "Single product"],
    ["POST /trigger/burst?size=N", "Inject a flash-sale burst (triggers REVENUE_SPIKE)"],
    ["POST /trigger/drain?product_id=N&times=M", "Hammer one SKU (triggers LOW_STOCK)"],
    ["WS /stream/orders", "Live JSON orders as they publish — any client can tap"],
    ["GET /docs", "Swagger UI"],
  ], "Route", "Purpose", [3000, 6360]),
  H3("The order-generator loop (simplified)"),
  Code(
    "async def order_generator_loop(state: AppState):\n" +
    "    while True:\n" +
    "        # 1. build one synthetic order against the REAL catalog\n" +
    "        order = build_order(state.products, state.basket_stats)\n\n" +
    "        # 2. publish to Kafka (downstream: Spark)\n" +
    "        state.producer.produce(\n" +
    "            topic=\"orders\",\n" +
    "            key=order[\"order_id\"].encode(),\n" +
    "            value=json.dumps(order, default=str).encode(),\n" +
    "        )\n" +
    "        state.producer.poll(0)\n\n" +
    "        # 3. fan out to every connected WebSocket subscriber\n" +
    "        for q in list(state.subscribers):\n" +
    "            if not q.full():\n" +
    "                q.put_nowait(order)\n\n" +
    "        state.orders_sent += 1\n" +
    "        await asyncio.sleep(random.uniform(2.0, 5.0))"
  ),
  H3("Why a single process?"),
  Bullet("Zero IPC: the generator and the WS broadcaster share memory."),
  Bullet("FastAPI lifespan hooks start/stop the background task cleanly."),
  Bullet("Burst + drain are just state flags flipped by HTTP handlers — no queueing."),
  Note("State is held in an AppState dataclass: products list, basket stats, Kafka producer, set of asyncio.Queue subscribers, burst counter, drain target."),
);

// 3.3 Kafka
children.push(
  H2("3.3 Kafka — the Replayable Event Bus"),
  P("Kafka sits between the producer (FastAPI) and the consumer (Spark). Two topics: orders (3 partitions) and inventory-updates (reserved for a future reverse channel)."),
  H3("Why Kafka and not a plain queue?"),
  Bullet("Durability — messages survive consumer crashes."),
  Bullet("Replay — a new consumer can start at offset 0 and replay history."),
  Bullet("Multi-consumer — the anomaly detector could read the stream directly if we wanted."),
  Bullet("Partitioning — future horizontal scale without code changes."),
  H3("Local deployment"),
  P("Kafka + Zookeeper + Kafka UI run in Docker via docker/docker-compose.yml. Kafka UI is on http://localhost:8080 and shows topic offsets + consumer lag — invaluable for debugging Spark."),
);

// 3.4 Spark
children.push(
  H2("3.4 Spark Structured Streaming — the Accountant"),
  P("The largest single file in the project (streaming/stream_processor.py). It reads Kafka as a structured stream, parses JSON with an explicit schema, applies a 10-minute watermark, and runs three parallel computations per micro-batch."),
  H3("The watermark"),
  Code(
    "parsed = (stream\n" +
    "    .selectExpr(\"CAST(value AS STRING) as json\")\n" +
    "    .select(from_json(\"json\", ORDER_SCHEMA).alias(\"o\"))\n" +
    "    .select(\"o.*\")\n" +
    "    .withWatermark(\"order_timestamp\", \"10 minutes\"))"
  ),
  P("A watermark tells Spark \"events older than X are ignored\". 10 minutes balances two things: giving a late order a fair chance to join its correct 1-minute window, and bounding the in-memory state Spark has to keep."),
  H3("The foreachBatch sink"),
  P("Instead of writing one stream to one sink, we use foreachBatch to write to five places atomically per micro-batch:"),
  Numbered("Raw orders → orders (append)"),
  Numbered("Exploded items → order_items (append)"),
  Numbered("1-min revenue aggregate → sales_metrics (staging-table upsert)"),
  Numbered("1-min per-product aggregate → product_sales_metrics (staging-table upsert)"),
  Numbered("products.stock_quantity decrement + inventory_log insert + LOW_STOCK alerts"),
  H3("The staging-table upsert pattern"),
  P("Spark JDBC can only INSERT. To achieve idempotent minute-level aggregates we write to a staging table and then MERGE via raw SQL:"),
  Code(
    "# Step 1: Spark writes the minute's aggregate to _stg_sales_metrics (append)\n" +
    "batch_df.write.jdbc(url, \"_stg_sales_metrics\", mode=\"append\", properties=props)\n\n" +
    "# Step 2: MERGE from staging into the real table\n" +
    "cursor.execute(\"\"\"\n" +
    "    INSERT INTO sales_metrics (window_start, window_end, revenue, order_count)\n" +
    "    SELECT window_start, window_end, revenue, order_count FROM _stg_sales_metrics\n" +
    "    ON DUPLICATE KEY UPDATE\n" +
    "        revenue = VALUES(revenue),\n" +
    "        order_count = VALUES(order_count)\n" +
    "\"\"\")\n" +
    "cursor.execute(\"TRUNCATE TABLE _stg_sales_metrics\")"
  ),
  P("Why this matters: if Spark replays a micro-batch (on restart or failure) the final numbers don't double. Idempotency is the whole point of streaming semantics."),
  H3("Inventory decrement + LOW_STOCK"),
  Code(
    "for row in batch_df.collect():\n" +
    "    cur.execute(\n" +
    "        \"UPDATE products SET stock_quantity = GREATEST(stock_quantity - %s, 0) \"\n" +
    "        \"WHERE product_id = %s\",\n" +
    "        (row.qty, row.product_id),\n" +
    "    )\n" +
    "    cur.execute(\"INSERT INTO inventory_log (...) VALUES (...)\", ...)\n\n" +
    "# After all decrements, emit LOW_STOCK alerts (10-min dedupe guard)\n" +
    "cur.execute(\"\"\"\n" +
    "    INSERT INTO alerts (alert_type, severity, product_id, detected_value, threshold_value, message)\n" +
    "    SELECT 'LOW_STOCK', 'WARNING', p.product_id, p.stock_quantity, p.reorder_threshold,\n" +
    "           CONCAT(p.name, ' stock at ', p.stock_quantity)\n" +
    "    FROM products p\n" +
    "    WHERE p.stock_quantity <= p.reorder_threshold\n" +
    "      AND NOT EXISTS (\n" +
    "        SELECT 1 FROM alerts a\n" +
    "        WHERE a.product_id = p.product_id\n" +
    "          AND a.alert_type = 'LOW_STOCK'\n" +
    "          AND a.alert_time >= NOW() - INTERVAL 10 MINUTE\n" +
    "      )\n" +
    "\"\"\")"
  ),
);

// 3.5 MySQL
children.push(
  H2("3.5 MySQL — the Source of Truth"),
  P("Eight tables, all created by database/schema.sql on first docker-compose up:"),
  TwoColTable([
    ["products", "Dimension. 20 rows post-sync. price, stock, threshold, popularity, rating."],
    ["orders", "Row-level fact. one row per order. total_amount, customer_id, timestamp."],
    ["order_items", "Fact detail. one row per line item. product_id, quantity, unit_price."],
    ["sales_metrics", "1-min aggregate. window_start/end, revenue, order_count. Primary key: window_start."],
    ["product_sales_metrics", "1-min per-product aggregate. Primary key: (window_start, product_id)."],
    ["inventory_log", "Append-only. every decrement logged with before/after quantities."],
    ["alerts", "LOW_STOCK, REVENUE_SPIKE, KPI_VIOLATION. severity ENUM, resolved flag, detected_value."],
    ["kpi_thresholds", "Config-as-data. metric_name, warning_threshold, critical_threshold, comparison, window_minutes."],
  ], "Table", "Purpose", [2800, 6560]),
  H3("Primary-key choices"),
  Bullet("sales_metrics uses window_start as the PK — so the upsert pattern above is the natural way to idempotently update a minute."),
  Bullet("product_sales_metrics uses (window_start, product_id) — composite key, same trick."),
  Bullet("orders uses order_id (UUID) — deduplicates if Spark replays."),
);

// 3.6 Anomaly
children.push(
  H2("3.6 Anomaly Detector — the Suspicious Auditor"),
  P("anomaly/detector.py runs as its own Python process. Every 60 seconds it pulls sales_metrics and decides whether the latest minute is anomalous."),
  H3("Two strategies, one detector"),
  Code(
    "df = pd.read_sql(\"SELECT * FROM sales_metrics ORDER BY window_start DESC LIMIT 120\", conn)\n\n" +
    "if len(df) < 15:\n" +
    "    # cold start — z-score on revenue\n" +
    "    mean, std = df.revenue.mean(), df.revenue.std()\n" +
    "    latest = df.iloc[0].revenue\n" +
    "    if std > 0 and (latest - mean) / std > 3.0:   # only high side\n" +
    "        emit_alert(latest, 'z-score > 3', severity='WARNING')\n" +
    "else:\n" +
    "    # fit Isolation Forest on [revenue, order_count]\n" +
    "    clf = IsolationForest(contamination=0.05, n_estimators=150, random_state=42)\n" +
    "    clf.fit(df[['revenue', 'order_count']])\n" +
    "    score = clf.score_samples(df[['revenue', 'order_count']].iloc[[0]])[0]\n" +
    "    latest = df.iloc[0].revenue\n" +
    "    median = df.revenue.median()\n" +
    "    if score < threshold and latest > median:\n" +
    "        emit_alert(latest, f'IF score={score:.3f}', severity='CRITICAL')"
  ),
  H3("Why both?"),
  Bullet("z-score needs almost no data — works from minute 1."),
  Bullet("Isolation Forest captures joint outliers (high revenue + low order count = suspicious fraud-like pattern) that z-score misses."),
  Bullet("Both filter out the low side (drops are handled by the KPI evaluator's revenue_drop_pct, which has richer context)."),
  Bullet("30-minute dedupe prevents alert storms from a single sustained burst."),
);

// 3.7 KPI
children.push(
  H2("3.7 KPI Evaluator — the Rule-book Enforcer"),
  P("SLOs expressed as rows in kpi_thresholds:"),
  Code(
    "metric_name        window_minutes  comparison  warning  critical\n" +
    "revenue_per_5min   5               less_than   100      50\n" +
    "orders_per_5min    5               less_than   5        2\n" +
    "low_stock_count    5               more_than   3        5\n" +
    "avg_order_value    10              less_than   30       15\n" +
    "revenue_drop_pct   15              more_than   30       50"
  ),
  P("The evaluator computes each metric over its configured window, compares to warning/critical, and writes a KPI_VIOLATION alert if breached (5-min dedupe)."),
  H3("Why this design?"),
  Bullet("Adding a new KPI = one INSERT, zero code deploys."),
  Bullet("Product and engineering can tune thresholds without a PR."),
  Bullet("The evaluator is ~150 lines because all the \"rules\" live in SQL rows."),
);

// 3.8 Power BI
children.push(
  H2("3.8 Power BI — the Big TV on the Wall"),
  P("Four pages, DirectQuery against MySQL, 1-minute page auto-refresh, 25+ DAX measures."),
  TwoColTable([
    ["Page 1: Live Ops", "KPI cards (revenue, AOV, orders), revenue sparkline, active alerts list."],
    ["Page 2: Product Performance", "Top products by revenue, category breakdown, stock vs threshold bar."],
    ["Page 3: Alerts & Anomalies", "Alert timeline, severity distribution, detected_value deltas."],
    ["Page 4: Ops Health", "KPI violations heatmap, ingestion lag, worker heartbeats."],
  ], "Page", "Contents", [2400, 6960]),
  H3("Why DirectQuery?"),
  Bullet("Aggregates are pre-computed in MySQL (sales_metrics), so DirectQuery is cheap — one query per visual per minute."),
  Bullet("No import/refresh schedule to manage — the dashboard is always as fresh as the database."),
  Bullet("Sub-second query latency for minute-level aggregates over 24h of history."),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 4. CODE WALKTHROUGHS
// ===========================================================================
children.push(
  H1("4. Key Code Walkthroughs"),
  P("Below are the four most interview-worthy snippets, annotated line by line. If you can defend these four, you can defend the whole project."),

  H2("4.1 Order Generation — api/order_engine.py"),
  Code(
    "def build_order(products, basket_stats):\n" +
    "    # 1. sample basket size from real /carts distribution\n" +
    "    n_items = random.choices(basket_stats.sizes, weights=basket_stats.size_weights)[0]\n\n" +
    "    # 2. popularity-weighted product pick (sampling without replacement)\n" +
    "    weights = [p.popularity_weight for p in products]\n" +
    "    picks = random.choices(products, weights=weights, k=n_items)\n\n" +
    "    # 3. per-item quantity from real /carts distribution\n" +
    "    items = []\n" +
    "    for p in picks:\n" +
    "        qty = random.choices(basket_stats.qtys, weights=basket_stats.qty_weights)[0]\n" +
    "        items.append({\n" +
    "            \"product_id\": p.product_id,\n" +
    "            \"name\": p.name,\n" +
    "            \"quantity\": qty,\n" +
    "            \"unit_price\": float(p.price),\n" +
    "            \"subtotal\": round(qty * p.price, 2),\n" +
    "        })\n\n" +
    "    return {\n" +
    "        \"order_id\": str(uuid4()),\n" +
    "        \"customer_id\": f\"C-{random.randint(0, 9999):04d}\",\n" +
    "        \"order_timestamp\": datetime.utcnow().isoformat(),\n" +
    "        \"items\": items,\n" +
    "        \"total_amount\": round(sum(it['subtotal'] for it in items), 2),\n" +
    "    }"
  ),
  P("Interview angle: \"Why weighted sampling?\" — because uniform sampling would make every SKU equally popular, which is never true. Real catalogs have a long tail; popularity_weight (derived from real rating.count) preserves the shape."),

  H2("4.2 Spark foreachBatch Sink — streaming/stream_processor.py"),
  Code(
    "def write_batch(batch_df, batch_id):\n" +
    "    if batch_df.rdd.isEmpty():\n" +
    "        return\n\n" +
    "    batch_df.cache()   # will be scanned multiple times\n\n" +
    "    # 1. raw orders\n" +
    "    (batch_df.drop('items')\n" +
    "        .write.jdbc(URL, 'orders', mode='append', properties=PROPS))\n\n" +
    "    # 2. explode items -> order_items\n" +
    "    items = batch_df.select('order_id', F.explode('items').alias('it'))\n" +
    "    (items.select('order_id', 'it.product_id', 'it.quantity', 'it.unit_price', 'it.subtotal')\n" +
    "        .write.jdbc(URL, 'order_items', mode='append', properties=PROPS))\n\n" +
    "    # 3. 1-min revenue agg -> staging -> upsert\n" +
    "    agg = (batch_df\n" +
    "        .groupBy(F.window('order_timestamp', '1 minute'))\n" +
    "        .agg(F.sum('total_amount').alias('revenue'),\n" +
    "             F.count('*').alias('order_count')))\n" +
    "    (agg.write.jdbc(URL, '_stg_sales_metrics', mode='append', properties=PROPS))\n" +
    "    merge_sales_metrics()   # SQL UPSERT then TRUNCATE staging\n\n" +
    "    # 4. per-product agg (same pattern)\n" +
    "    ...\n\n" +
    "    # 5. inventory + low-stock\n" +
    "    decrement_stock_and_check(items)\n\n" +
    "    batch_df.unpersist()"
  ),
  P("Interview angles:"),
  Bullet("Why cache? We scan batch_df five times — one JDBC write per scan. Caching saves four re-executions of the entire streaming DAG for this batch."),
  Bullet("Why not write the agg directly? JDBC only supports INSERT. Upserts need raw SQL, hence the staging table."),
  Bullet("Why collect for inventory? A batch is small (seconds of data), so collect() is safe. For larger batches we'd use foreachPartition."),

  H2("4.3 Anomaly Detector — anomaly/detector.py"),
  Code(
    "while True:\n" +
    "    df = pd.read_sql(SALES_QUERY, conn)\n" +
    "    if df.empty:\n" +
    "        time.sleep(60); continue\n\n" +
    "    latest = df.iloc[0]\n" +
    "    if len(df) < 15:\n" +
    "        mu, sd = df.revenue.mean(), df.revenue.std(ddof=0)\n" +
    "        z = (latest.revenue - mu) / sd if sd > 0 else 0\n" +
    "        is_anom = z > 3.0\n" +
    "        reason = f'z-score={z:.2f}'\n" +
    "    else:\n" +
    "        clf = IsolationForest(contamination=0.05, n_estimators=150, random_state=42)\n" +
    "        X = df[['revenue', 'order_count']].values\n" +
    "        clf.fit(X)\n" +
    "        score = clf.score_samples(X[:1])[0]\n" +
    "        is_anom = (score < ANOMALY_THRESHOLD) and (latest.revenue > df.revenue.median())\n" +
    "        reason = f'IF score={score:.3f}'\n\n" +
    "    if is_anom and not_recently_alerted(latest.window_start):\n" +
    "        insert_alert('REVENUE_SPIKE', latest.revenue, reason)\n\n" +
    "    time.sleep(60)"
  ),
  P("Interview angle: \"Why the 'latest > median' guard on Isolation Forest?\" — because we only care about revenue spikes, not drops. Drops have a dedicated KPI (revenue_drop_pct) that can compare against a reference window, which IF can't do in a 1D feature space."),

  H2("4.4 KPI Evaluator — kpi/evaluator.py"),
  Code(
    "def evaluate_row(t):\n" +
    "    value = compute_metric(t.metric_name, t.window_minutes)\n" +
    "    breached_critical = compare(value, t.critical_threshold, t.comparison)\n" +
    "    breached_warning  = compare(value, t.warning_threshold,  t.comparison)\n" +
    "    if breached_critical:\n" +
    "        emit('KPI_VIOLATION', 'CRITICAL', t.metric_name, value, t.critical_threshold)\n" +
    "    elif breached_warning:\n" +
    "        emit('KPI_VIOLATION', 'WARNING',  t.metric_name, value, t.warning_threshold)\n\n" +
    "def compare(value, threshold, op):\n" +
    "    return {\n" +
    "        'more_than': value > threshold,\n" +
    "        'less_than': value < threshold,\n" +
    "        'equal_to':  value == threshold,\n" +
    "    }[op]"
  ),
  P("Interview angle: \"What's the trade-off with config-as-data?\" — pro: fast iteration, no deploys. Con: no type-checking on rules, and a typo in comparison silently no-ops. Mitigation: the evaluator validates the enum on load and refuses to start if any row is malformed."),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 5. DATABASE SCHEMA
// ===========================================================================
children.push(
  H1("5. Database Schema"),
  H2("5.1 Relationships"),
  Code(
    "products ||--o{ order_items            (one product, many line items)\n" +
    "orders   ||--o{ order_items            (one order, many line items)\n" +
    "products ||--o{ product_sales_metrics  (one product, many minutes)\n" +
    "products ||--o{ inventory_log          (one product, many mutations)\n" +
    "kpi_thresholds ||--o{ alerts           (one rule, many violations)"
  ),
  H2("5.2 Indices that matter"),
  Bullet("sales_metrics(window_start) — PK, used by DirectQuery's time-range filter."),
  Bullet("product_sales_metrics(window_start, product_id) — composite PK, used by the per-product table viz."),
  Bullet("alerts(alert_time DESC) — non-PK index, backs the live alerts list."),
  Bullet("orders(order_timestamp) — non-PK index, backs time-filtered aggregates that bypass the pre-aggregation (rare)."),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 6. OPERATIONS
// ===========================================================================
children.push(
  H1("6. Operating the Stack"),
  H2("6.1 Start everything"),
  Code(
    "python -m venv .venv\n" +
    ".venv/Scripts/activate    # windows\n" +
    "pip install -r requirements.txt\n" +
    "cp .env.example .env\n\n" +
    "docker compose -f docker/docker-compose.yml up -d\n" +
    "python scripts/orchestrator.py up       # hydrates catalog, starts Spark + API + detectors\n" +
    "python scripts/orchestrator.py status   # health check"
  ),
  H2("6.2 Demo triggers"),
  Code(
    "# flash-sale burst -> REVENUE_SPIKE inside ~60s\n" +
    "python scripts/demo_controller.py burst --size 60\n\n" +
    "# drain a SKU -> LOW_STOCK alert\n" +
    "python scripts/demo_controller.py drain --product 1 --times 40\n\n" +
    "# reset state\n" +
    "python scripts/demo_controller.py clear-alerts\n" +
    "python scripts/demo_controller.py reset-stock\n\n" +
    "# tail a worker log\n" +
    "python scripts/orchestrator.py logs spark --tail 100"
  ),
  H2("6.3 What to check when something breaks"),
  TwoColTable([
    ["No orders flowing", "logs/api.log — products loaded? Kafka up? then logs/spark.log"],
    ["Power BI shows stale data", "check sales_metrics for recent window_start; check Spark log for JDBC errors"],
    ["No alerts firing", "logs/anomaly.log + logs/kpi.log; verify kpi_thresholds has rows"],
    ["LOW_STOCK not triggering", "query products — is stock_quantity actually dropping? Is dedupe guard hiding repeats?"],
    ["Kafka consumer lag climbing", "Kafka UI http://localhost:8080; maybe Spark died — status + tail log"],
  ], "Symptom", "First thing to check", [2600, 6760]),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 7. INTERVIEW Q&A
// ===========================================================================
children.push(
  H1("7. Interview Q&A"),
  P("The questions you're most likely to get, with tight answers you can actually deliver out loud."),
);

const qa = [
  ["Walk me through the project in 90 seconds.",
   "Real-time e-commerce monitor. A FastAPI service hydrates a real product catalog from FakeStoreAPI and synthesizes orders against it every 2–5 seconds — baskets are shaped from real /carts data. Orders publish to Kafka. Spark Structured Streaming reads Kafka, uses a 10-minute watermark and 1-minute tumbling windows, and in a single foreachBatch writes raw orders, exploded line items, two windowed aggregates (revenue and per-product), inventory decrements, and LOW_STOCK alerts — all into MySQL using a staging-table upsert for idempotency. Two detectors poll MySQL: one does z-score then Isolation Forest for revenue spikes; the other checks SLOs that live as rows in a kpi_thresholds table. Power BI runs DirectQuery on MySQL with a 1-minute page refresh across four pages."],
  ["Why Kafka and not just an HTTP webhook?",
   "Durability, replay, and multi-consumer. If Spark crashes it resumes at its last committed offset — no lost events. A second consumer (say, a real-time personalization service) could tap the same stream without touching the producer. Webhooks give none of that."],
  ["Why Spark Structured Streaming and not Kafka Streams or Flink?",
   "Python ecosystem parity — the anomaly detector is sklearn, the producer is confluent-kafka, the orchestrator is argparse. Spark's PySpark API keeps the whole stack in one language. foreachBatch also lets me write to multiple sinks atomically per micro-batch, which Kafka Streams doesn't do naturally. Flink would work too; the trade-off is operator familiarity."],
  ["What does the 10-minute watermark actually do?",
   "It tells Spark 'don't hold state for events older than 10 minutes past the current max event-time.' With 1-minute windows, that gives any given window ~10 minutes to accept late arrivals before Spark finalizes it and evicts its state. Longer watermark = more tolerance, more memory. 10 is enough for demo latency."],
  ["Why foreachBatch instead of a native sink?",
   "Two reasons: (1) JDBC's built-in sink only does INSERT, but I need upserts on the minute-level aggregates — so I write to a staging table and MERGE with raw SQL inside foreachBatch. (2) I need to write to five destinations atomically per batch. foreachBatch gives me transactional control."],
  ["Walk me through the staging-table upsert pattern.",
   "Spark writes the minute's aggregate to _stg_sales_metrics in append mode. Then inside the same foreachBatch I open a JDBC connection and run 'INSERT INTO sales_metrics ... SELECT ... FROM _stg_sales_metrics ON DUPLICATE KEY UPDATE', then TRUNCATE _stg_sales_metrics. The primary key on sales_metrics is window_start, so a re-run of the same batch overwrites identical rows — idempotent."],
  ["Why two anomaly-detection strategies?",
   "Cold start. Isolation Forest needs enough history to learn what 'normal' looks like — I use 15 minutes as the cut-over. Below 15 rows of sales_metrics, I fall back to z-score on revenue. After 15, I fit Isolation Forest on [revenue, order_count] and flag outliers with a score below threshold, guarded to only alert on the high side of the median (spikes, not drops)."],
  ["Why is the KPI evaluator separate from the anomaly detector?",
   "Different problem. Anomalies are statistical — 'this is unusual compared to history.' KPIs are deterministic business rules — 'revenue must be > $100 per 5 minutes or we page someone.' They don't share code because one is model-driven and the other is threshold-driven. The KPI rules live as rows in kpi_thresholds so product can tune SLOs without a deploy."],
  ["Why DirectQuery in Power BI instead of Import mode?",
   "Aggregates are pre-computed in sales_metrics — one SELECT per visual per minute is cheap. Import mode would require a refresh schedule and always lag the data. DirectQuery gives us 1-minute-fresh dashboards with no ETL on the BI side."],
  ["What prevents duplicate alerts from firing every loop?",
   "A dedupe guard in SQL. For LOW_STOCK it's 10 minutes, for REVENUE_SPIKE 30 minutes, for KPI_VIOLATION 5 minutes. The INSERT ... WHERE NOT EXISTS clause checks if an equivalent alert already fired in the guard window."],
  ["How would you scale this to 10,000 orders per second?",
   "(1) Increase Kafka orders topic partitions to match Spark executor count. (2) Move MySQL to a columnar analytics store like BigQuery or ClickHouse — the minute aggregates become continuous-aggregate materialized views. (3) Replace the Python anomaly detector with a Spark ML model running inside the same streaming job. (4) Switch Power BI from DirectQuery to a dedicated BI cache layer. The architecture doesn't fundamentally change — Kafka + Spark + warehouse + BI is the same shape, just bigger."],
  ["How would you deploy this to GCP?",
   "Pub/Sub replaces Kafka; Dataflow (Apache Beam) or Dataproc replaces Spark; BigQuery replaces MySQL; Looker Studio replaces Power BI; the FastAPI service runs on Cloud Run. The code changes are surprisingly small because the interfaces are all decoupled — swap the Kafka producer for a Pub/Sub producer, swap JDBC for BigQuery Storage Write API. docs/CLOUD_DEPLOYMENT.md has the full mapping."],
  ["What's the weakest part of the design?",
   "The products table is single-row-per-SKU and gets updated in place by the inventory decrement — that row-level contention would bite at scale. A more correct design is an append-only inventory_events stream with stock_quantity as a materialized view over event sums. That gives you history, replay, and no write contention."],
  ["How would you test this end-to-end?",
   "Unit tests on order_engine.build_order and the KPI comparator. Integration tests that spin up Kafka+MySQL in testcontainers, pump 100 orders, and assert sales_metrics totals. Streaming tests using Spark's MemoryStream source to verify the watermark + upsert logic without Kafka. Chaos tests that kill Spark mid-batch and verify idempotency on restart."],
  ["Why FakeStoreAPI and not Best Buy or Etsy?",
   "Free + no-auth + immediately runnable for a reviewer. Best Buy's API requires a key and has rate limits; Etsy needs OAuth. For a portfolio project where reviewers should be able to git clone and run in five minutes, the friction matters more than the realism. The catalog shape is identical, so swapping later is a config change."],
  ["Where's the event-time vs processing-time distinction?",
   "order_timestamp (set by FastAPI at generation) is the event time. Spark's watermark is on order_timestamp, not on the Kafka ingest time. Windows are event-time based — so a delayed order still lands in its correct minute bucket up to the watermark limit."],
  ["Why don't you use schema registry?",
   "Overkill for one producer and one consumer at demo scale. If we added a second producer or a JVM consumer I'd add Confluent Schema Registry + Avro; right now it's plain JSON with an explicit Spark schema in stream_processor.py."],
  ["How do you handle schema evolution?",
   "Two parts. Kafka payload: additive-only JSON (never remove a field, never change a type). MySQL: migrations in database/migrations/ applied idempotently (ALTER TABLE IF NOT EXISTS). For destructive changes I'd blue/green the consumer."],
  ["What's the observability story?",
   "Every worker logs to logs/<name>.log. Kafka UI at :8080 shows consumer lag. The alerts table is itself the operational feed — every anomaly and violation is a row with severity and detected_value. In production I'd add Prometheus metrics on the FastAPI service and Spark's built-in StreamingQuery metrics exported to Grafana."],
  ["What would you do differently next time?",
   "Event-sourced inventory (mentioned above). Typed Kafka schemas from day one. Spark on k8s from day one — local spark-submit is fine for demo but hides resource limits. And I'd front MySQL with a read replica for Power BI so the BI query load can't slow down Spark's writes."],
];

qa.forEach(([q, a], i) => {
  children.push(
    new Paragraph({
      spacing: { before: 160, after: 40 },
      children: [
        new TextRun({ text: `Q${i + 1}. `, bold: true, color: "1F3864" }),
        new TextRun({ text: q, bold: true }),
      ],
    }),
    Pmulti([
      new TextRun({ text: "A. ", bold: true, color: "2E75B6" }),
      new TextRun(a),
    ]),
  );
});

children.push(new Paragraph({ children: [new PageBreak()] }));

// ===========================================================================
// 8. ALTERNATIVE APPROACHES (per pipeline step)
// ===========================================================================
children.push(
  H1("8. Alternative Approaches for Every Step"),
  P("For every decision in this pipeline there were three or four credible alternatives. The point of this chapter isn't to defend the choices that were made — it's to show that each was made with the others in the room. When an interviewer asks \"what else could you have done?\", these are the answers."),
  P("Each section lists the main alternatives in a consistent shape: a short description, what it would buy you, what it would cost you, and the one-line reason it lost out."),
);

// 8.1 Data source
children.push(
  H2("8.1 Step: Data Source"),
  P("The project needed a real product catalog plus a stream of transactions. No public API exposes live order data, so the decision splits in two: where does the catalog come from, and how are transactions synthesized."),
  H3("Alternatives considered for the catalog"),
  TwoColTable([
    ["FakeStoreAPI (chosen)",
     "Pros: free, no-auth, real product identity, real /carts for basket shape, zero friction for reviewers. Cons: only 20 SKUs, static data."],
    ["Best Buy Developer API",
     "Pros: tens of thousands of real SKUs, real pricing + availability, enterprise-grade. Cons: requires an API key, has rate limits, reviewer can't run `git clone && make up` without signing up."],
    ["Etsy Open API",
     "Pros: huge long-tail catalog, real category taxonomy. Cons: OAuth 1.0a handshake, category metadata is inconsistent, rate limits are stricter."],
    ["Kaggle Instacart dataset",
     "Pros: 3M real orders, real basket co-occurrence, industry-gold dataset. Cons: batch file, not a stream — you'd have to \"replay\" a CSV; no prices (only product_id + reordered flag); demo becomes an offline ETL, not live."],
    ["Amazon Product Advertising API",
     "Pros: the real thing. Cons: Associates account required, approval can take days, ToS restricts redistribution of product data."],
    ["Pure Faker library",
     "Pros: zero external dependency, infinite catalog. Cons: fake product names fool no one — the project loses credibility as anything other than a code exercise."],
  ], "Option", "Trade-off", [2600, 6760]),
  Note("Why FakeStoreAPI won: the project is a portfolio demo, so setup friction is the single most important constraint. A reviewer who has to sign up for Best Buy's API before they can run the demo usually just doesn't. FakeStoreAPI + /carts-derived basket shapes gets us 80% of the realism at 0% of the friction."),
  H3("Alternatives for transaction generation"),
  TwoColTable([
    ["Uniform random picks", "Pros: simplest possible. Cons: every SKU equally popular — no Pareto tail, no interesting aggregates, fake-looking charts."],
    ["Faker's provider system", "Pros: wide library of generators. Cons: none of them know about our catalog; we'd write the weighting logic anyway."],
    ["Replay real /orders from a CSV (Kaggle Instacart)", "Pros: real basket co-occurrence and temporal patterns. Cons: pinned to one point in time; no way to inject bursts or drain on demand."],
    ["Weighted sampling from rating.count + real /carts basket sizes (chosen)", "Pros: popular items sell more (Pareto-like), basket sizes and quantities come from real data, supports on-demand bursts via /trigger/*. Cons: timestamps are ours, so we can't claim market realism."],
  ], "Option", "Trade-off", [3000, 6360]),
);

// 8.2 Live edge / producer
children.push(
  H2("8.2 Step: Live Edge Service (Order Generator + Producer)"),
  P("Something has to host the order-generator loop, publish to Kafka, and expose a control surface for the demo triggers."),
  TwoColTable([
    ["FastAPI + uvicorn (chosen)",
     "Pros: async-first so the Kafka producer, WebSocket fan-out, and HTTP handlers share one loop; auto-generated Swagger UI; tiny mental model. Cons: adds a web framework to debug."],
    ["Plain Python script with a while-True loop",
     "Pros: fewest moving parts. Cons: no HTTP surface means no /trigger/*, no WebSocket broadcast, no /docs. Demos lose their interactivity."],
    ["Flask + Flask-SocketIO",
     "Pros: familiar to many devs, mature. Cons: sync-by-default; gevent/eventlet needed to run the background task, more boilerplate for WebSockets, no built-in OpenAPI."],
    ["Node.js + Express + kafkajs",
     "Pros: fast WebSocket fan-out, kafkajs is excellent. Cons: splits the project across two runtimes (Python for Spark + detectors, JS for the edge); more CI surface."],
    ["Go + Sarama + Gorilla WebSocket",
     "Pros: lowest latency, single binary deploy. Cons: Go adds a third language; the project's audience (data teams) overwhelmingly reads Python better."],
    ["Kafka REST Proxy (Confluent)",
     "Pros: no custom producer code. Cons: still need something to run the generator loop; adds another service to stand up."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why FastAPI won: the single-language Python stack is worth a lot for a portfolio project (reviewers can read everything), and FastAPI's async model genuinely fits the shape of the work — one loop that produces, another loop that serves, sharing memory."),
);

// 8.3 Message bus
children.push(
  H2("8.3 Step: The Message Bus"),
  P("A component is needed between the producer and the stream processor that buffers, persists, and allows replay."),
  TwoColTable([
    ["Apache Kafka (chosen)",
     "Pros: durable, replayable, partitioned, first-class Spark connector, the de facto industry standard. Cons: heaviest local footprint (Zookeeper + broker)."],
    ["Redis Streams",
     "Pros: one-container install, simple API, decent throughput. Cons: retention is tied to memory; no native Spark connector; cluster mode is newer and less battle-tested."],
    ["RabbitMQ / AMQP",
     "Pros: mature, flexible routing (exchanges + bindings). Cons: queue-semantics not log-semantics — consumers compete for messages rather than replay; Spark integration is awkward."],
    ["Amazon Kinesis / GCP Pub/Sub",
     "Pros: managed, zero ops. Cons: requires a cloud account + cost + auth — kills the local-first demo."],
    ["Apache Pulsar",
     "Pros: tiered storage, unified stream + queue semantics. Cons: smaller Spark ecosystem; learning curve; overkill at demo scale."],
    ["NATS JetStream",
     "Pros: tiny footprint, fast, simple. Cons: Spark connector is community-maintained; fewer production case studies in data-pipeline roles."],
    ["Plain TCP socket / WebSocket fan-out only",
     "Pros: zero extra infra. Cons: no durability — if Spark crashes, events are lost forever; no replay for late consumers."],
  ], "Option", "Trade-off", [2600, 6760]),
  Note("Why Kafka won: it's the answer an interviewer expects, and it's the correct one at any production scale. Using it locally (via Docker) proves familiarity with the real tooling rather than a toy substitute."),
);

// 8.4 Stream processor
children.push(
  H2("8.4 Step: Stream Processor"),
  P("Something has to consume the topic, window by event time, aggregate, and write to storage."),
  TwoColTable([
    ["Spark Structured Streaming (chosen)",
     "Pros: PySpark keeps the whole stack in Python; native watermarking; foreachBatch enables atomic multi-sink writes + raw SQL; great tooling. Cons: micro-batch latency floor (~seconds), not true streaming."],
    ["Apache Flink",
     "Pros: true event-at-a-time streaming, sub-second latency, superior state management. Cons: primary API is Java/Scala; PyFlink is behind; less familiar to most data teams."],
    ["Kafka Streams",
     "Pros: zero extra infra (library, not a cluster), exactly-once baked in. Cons: JVM-only, no Python, no multi-sink transactional writes."],
    ["ksqlDB",
     "Pros: SQL-only, trivial to express the windowed aggregates. Cons: limited sink options (can't do raw SQL upsert to MySQL), ML integration awkward."],
    ["Apache Beam (on Dataflow / Direct Runner)",
     "Pros: portable — same code runs on Flink, Spark, or Dataflow. Cons: extra abstraction layer for no win at demo scale; Python SDK lags the Java SDK."],
    ["Hand-rolled Python consumer (confluent-kafka + pandas)",
     "Pros: zero framework. Cons: you reinvent watermarking, windowing, checkpointing, exactly-once — all the hard parts of streaming."],
    ["Faust (Python)",
     "Pros: Python-native streaming library. Cons: project activity slowed; less production hardening than Spark."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why Spark Structured Streaming won: the project needed event-time windows, watermarks, multi-sink writes, and Python — Spark is the only option that gives all four. Flink would win at scale but loses on language and team familiarity."),
);

// 8.5 Upsert mechanism
children.push(
  H2("8.5 Step: Idempotent Upsert into the Warehouse"),
  P("Spark JDBC can only INSERT, but minute-level aggregates need UPDATE-on-replay to be idempotent. How do we bridge that?"),
  TwoColTable([
    ["Staging table + ON DUPLICATE KEY UPDATE (chosen)",
     "Pros: uses MySQL's native upsert; clean separation (Spark appends, SQL merges); easy to reason about. Cons: staging table is briefly visible; TRUNCATE each batch is a minor hit."],
    ["Direct MERGE from Spark DataFrame",
     "Pros: no staging table. Cons: vanilla MySQL 8 has no MERGE statement; would need to switch DB or emulate with row-by-row upserts (slow)."],
    ["DELETE-then-INSERT in a transaction",
     "Pros: simple. Cons: writes double the data; WHERE clause must match exactly or you lose rows; transaction size grows unboundedly on wide batches."],
    ["Make the sink idempotent by primary-key design alone (INSERT IGNORE)",
     "Pros: no merge logic. Cons: on replay you'd ignore legitimately-updated rows — same window could end up with the old aggregate if Spark recomputes."],
    ["Write to Delta Lake / Apache Iceberg instead of MySQL",
     "Pros: native MERGE INTO, time travel. Cons: changes the whole storage layer; Power BI has limited direct support."],
    ["Materialized view computed from raw orders",
     "Pros: the aggregate is derived, not stored — always consistent. Cons: MySQL doesn't have incremental materialized views; recomputing on every read is slow at scale."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why staging + ON DUPLICATE KEY UPDATE won: it's the least-clever working solution. Every competing approach either changes the database, sacrifices correctness, or adds complexity that has to be maintained forever."),
);

// 8.6 Storage
children.push(
  H2("8.6 Step: Storage / Source of Truth"),
  P("Where do the orders, aggregates, and alerts actually live?"),
  TwoColTable([
    ["MySQL 8 (chosen)",
     "Pros: easiest Docker setup, best Power BI DirectQuery driver, universally familiar. Cons: row-based storage, no columnar compression, no incremental materialized views."],
    ["PostgreSQL",
     "Pros: better SQL (MERGE, array types, materialized views, window functions), richer JSON support. Cons: Power BI DirectQuery is worse for Postgres than MySQL; no major functional gain for this project."],
    ["ClickHouse",
     "Pros: columnar, blazing-fast aggregate queries, made for exactly this workload. Cons: different SQL dialect; Power BI connector is third-party; Docker setup more involved."],
    ["TimescaleDB (Postgres + time-series extension)",
     "Pros: continuous aggregates would replace our entire staging-table pattern. Cons: another extension to install; Power BI support same as Postgres."],
    ["DuckDB (embedded)",
     "Pros: zero server, fastest local analytical queries, perfect for notebook work. Cons: single-writer model breaks the moment you need concurrent Spark writes + Power BI reads."],
    ["BigQuery / Snowflake / Redshift",
     "Pros: the production answer at scale. Cons: cloud account + cost + auth; kills the local-first demo."],
    ["InfluxDB",
     "Pros: built for time-series; retention policies are a config line. Cons: proprietary query languages (Flux / InfluxQL) break the Power BI story."],
  ], "Option", "Trade-off", [2600, 6760]),
  Note("Why MySQL won: DirectQuery driver quality. The whole Power BI story hinges on the dashboard staying fast at 1-minute refresh against a live database, and MySQL + Power BI is a more polished path than any alternative. Cloud migration path to BigQuery is documented in docs/CLOUD_DEPLOYMENT.md."),
);

// 8.7 Anomaly detection
children.push(
  H2("8.7 Step: Anomaly Detection"),
  P("How do we decide whether a given minute's revenue is \"unusual\"?"),
  TwoColTable([
    ["z-score fallback + Isolation Forest (chosen)",
     "Pros: handles cold start (z-score works from minute 1), Isolation Forest captures joint outliers once history exists, fits in milliseconds. Cons: no seasonality; flat across weekdays vs weekends."],
    ["z-score only",
     "Pros: dead simple. Cons: assumes Gaussian, misses joint outliers (high revenue + low order count = fraud-like)."],
    ["Moving-average + standard-deviation bands (Bollinger-style)",
     "Pros: adaptive, visual, easy to explain. Cons: lags on sudden regime changes; single-variable only."],
    ["Seasonal naive + residual threshold",
     "Pros: cheap way to handle time-of-day / day-of-week seasonality. Cons: needs weeks of history to learn seasonality; overkill for a demo."],
    ["STL decomposition + residual z-score",
     "Pros: handles seasonality explicitly. Cons: same cold-start problem; extra dependency (statsmodels)."],
    ["Prophet (Facebook)",
     "Pros: seasonality + holidays + changepoints out of the box. Cons: heavy install (cmdstan), trains in seconds not milliseconds, API-designed for daily data."],
    ["LSTM / autoencoder reconstruction error",
     "Pros: captures complex temporal patterns. Cons: training infra, GPU, days of data, massive overkill."],
    ["River / online learning (incremental)",
     "Pros: no batch re-fit, no cold start. Cons: smaller ecosystem; harder to explain to non-ML interviewers."],
    ["SQL-only rules (e.g. \"flag if latest > 3 × median of last 60\")",
     "Pros: no Python, no model. Cons: brittle, arbitrary constants, not really anomaly detection — it's just a threshold."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why the two-strategy approach won: the cold-start problem is real and every alternative has the same weakness — either it needs history (and fails at minute 1) or it's so simple it misses joint outliers. Stacking z-score for cold start with Isolation Forest for steady state solves both without pretending the demo has weeks of training data."),
);

// 8.8 KPI rules
children.push(
  H2("8.8 Step: KPI / SLO Rules"),
  P("Where do the business thresholds live, and how do they get evaluated?"),
  TwoColTable([
    ["Config-as-data in a MySQL table (chosen)",
     "Pros: product edits SLOs with a SQL UPDATE — zero deploys; readable in any DB client; visible in Power BI as a dimension. Cons: no compile-time validation; typo in comparison silently no-ops."],
    ["Hard-coded Python constants",
     "Pros: type-checked, lint-checked, version-controlled. Cons: every threshold change is a PR + deploy; product can't tune without engineering."],
    ["YAML / TOML config file",
     "Pros: human-readable, type-validated with pydantic. Cons: still requires a deploy or file mount; drift between prod + staging files is common."],
    ["Rules engine (Drools, Open Policy Agent)",
     "Pros: expressive, auditable, supports complex compound rules. Cons: another service to run, massive overkill for five threshold rules."],
    ["Feature flag service (LaunchDarkly, Flagsmith)",
     "Pros: purpose-built for config-as-data with UI + audit log. Cons: external SaaS cost; kills the local-first story."],
    ["Git-ops: thresholds in a YAML file with auto-reload",
     "Pros: version history, PR review. Cons: slower iteration; requires branch + merge + sync for every tweak."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why config-as-data in SQL won: the evaluator is already talking to MySQL for everything else, and SLO rules are conceptually data (they change, they have history, they're queried by the dashboard). Making them a code artifact creates a false barrier. The no-op-on-typo risk is mitigated by validating the comparison enum on evaluator startup."),
);

// 8.9 BI layer
children.push(
  H2("8.9 Step: BI / Visualization"),
  P("Where does the dashboard live, and how fresh is the data it shows?"),
  TwoColTable([
    ["Power BI Desktop + DirectQuery (chosen)",
     "Pros: DAX is powerful for the KPI cards; DirectQuery means always-fresh data; wide industry familiarity. Cons: Desktop is Windows-only; Service tier needs a license."],
    ["Power BI Import mode",
     "Pros: fastest query performance (in-memory). Cons: refresh schedule required; dashboard always lags the data; undermines the point of real-time."],
    ["Tableau",
     "Pros: arguably better visualization grammar; cross-platform. Cons: Tableau Desktop licensing; less MySQL DirectQuery tuning community."],
    ["Looker / Looker Studio",
     "Pros: git-managed LookML or free Studio tier; great for teams. Cons: Looker is pricey; Studio Community Connectors for MySQL are janky."],
    ["Apache Superset",
     "Pros: open source, SQL-first, runs anywhere. Cons: another service to deploy; polish gap vs Power BI for executive dashboards."],
    ["Metabase",
     "Pros: easiest open-source BI to set up; beautiful defaults. Cons: limited custom calculations; no true equivalent of DAX measures."],
    ["Grafana",
     "Pros: best-in-class for ops dashboards; MySQL plugin works. Cons: not designed for business KPI cards; long-form analytics is awkward."],
    ["A custom React + D3 dashboard",
     "Pros: infinite flexibility. Cons: reinventing BI — weeks of work to get to parity with a 1-hour Power BI build."],
    ["Streamlit / Dash (Python)",
     "Pros: fits the Python stack; zero BI tool needed. Cons: not a real BI tool — missing drill-downs, cross-filters, proper slicers."],
  ], "Option", "Trade-off", [2600, 6760]),
  Note("Why Power BI DirectQuery won: the target audience for this project is data-analyst / BI-engineer roles, where Power BI is the expected skill. DirectQuery is the mode that actually demonstrates real-time — Import mode with a 5-minute refresh is what most Power BI projects do, and specifically not what this one is about."),
);

// 8.10 Orchestration
children.push(
  H2("8.10 Step: Orchestration / Process Management"),
  P("Something has to start everything in the right order, track PIDs, and let you tail logs."),
  TwoColTable([
    ["Custom Python orchestrator.py (chosen)",
     "Pros: zero extra dependencies, cross-platform, tailored to the stack, one command (`up`) boots everything. Cons: reinventing supervisor/systemd at small scale; PID-file registry is fragile."],
    ["docker-compose for everything (including Python workers)",
     "Pros: one compose file starts the entire stack; isolation by default. Cons: Spark driver in Docker complicates JDBC + host networking; `compose logs` is less ergonomic than per-worker log files."],
    ["Supervisor (supervisord)",
     "Pros: purpose-built process manager, auto-restart, log rotation. Cons: extra install; configuration-file overhead; not a natural fit for \"first-boot catalog sync then start workers\"."],
    ["systemd unit files (Linux only)",
     "Pros: production-grade, already installed. Cons: Linux-only kills the Windows developer story; users need sudo to edit units."],
    ["Makefile with phony targets",
     "Pros: universal. Cons: Windows lacks make by default; no PID tracking for `status`."],
    ["Apache Airflow",
     "Pros: DAG-based orchestration, great for batch. Cons: Airflow is for scheduled jobs, not long-running services — wrong tool."],
    ["Prefect / Dagster",
     "Pros: modern DAG orchestrators with real-time UIs. Cons: same category mismatch — they run tasks, not services."],
    ["Kubernetes (kind / minikube)",
     "Pros: production-realistic. Cons: hours of setup for a portfolio project; hides most of the moving parts behind YAML."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why the custom orchestrator won: it's ~250 lines and does exactly what this project needs — boot docker-compose, wait for Kafka + MySQL, run the catalog sync, then spawn four Python workers with per-component log files. Every heavier tool either pulls in an OS dependency (systemd), solves the wrong problem (Airflow), or adds setup burden the reviewer doesn't need."),
);

// 8.11 Containerization / deployment
children.push(
  H2("8.11 Step: Local Deployment Surface"),
  P("How does a reviewer actually run this thing on their laptop?"),
  TwoColTable([
    ["Docker Compose for infra, venv for Python (chosen)",
     "Pros: infra (Kafka, MySQL) is isolated and reproducible; Python is editable in-place for development; fastest inner loop. Cons: two things to set up instead of one."],
    ["Everything in Docker",
     "Pros: one command. Cons: slow iteration (rebuild on every Python change); Spark inside Docker has networking edge cases with JDBC to host MySQL."],
    ["Everything on host",
     "Pros: simplest to explain. Cons: reviewer has to install Kafka + MySQL + Zookeeper locally — enormous friction."],
    ["Vagrant / VirtualBox VM",
     "Pros: full isolation. Cons: VirtualBox licensing changes; heavy; slower than Docker."],
    ["Nix / devcontainer",
     "Pros: bit-exact reproducible. Cons: learning curve; excludes the many reviewers who won't install Nix to grade a portfolio project."],
    ["Cloud-only (Terraform + GCP / AWS)",
     "Pros: production-realistic from day one. Cons: reviewer needs a cloud account; setup is minutes-to-hours and costs money."],
  ], "Option", "Trade-off", [2800, 6560]),
  Note("Why Docker-for-infra + venv-for-Python won: it's the split every professional Python data team uses in practice. The parts that are hard to install locally (Kafka, MySQL) are containerized. The parts you iterate on all day (Python) stay native."),
);

// 8.12 How to talk about this in an interview
children.push(
  H2("8.12 How to Talk About These Trade-offs in an Interview"),
  P("The interviewer isn't checking that you picked the \"best\" tool. They're checking that you understand your tool's limits and can articulate the shape of the problem space. A good answer has four beats:"),
  Numbered("Name the choice. \"I used Spark Structured Streaming.\""),
  Numbered("Name 2–3 alternatives you considered. \"I considered Flink and Kafka Streams.\""),
  Numbered("Name the deciding constraint. \"The deciding constraint was keeping the stack in Python so the anomaly detector could share dataframes with the Spark job.\""),
  Numbered("Name what would tip you the other way. \"If the latency target were sub-second instead of minute-level, Flink wins.\""),
  Note("Interviewers call this \"showing your work.\" It turns a yes/no question (\"do you know Spark?\") into evidence that you think in trade-offs — which is the single most repeated signal in senior-engineer hiring loops."),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===========================================================================
// 9. DESIGN DECISIONS & TRADE-OFFS
// ===========================================================================
children.push(
  H1("9. Design Decisions & Trade-offs"),
  P("Every interesting system makes explicit trade-offs. Here are the ones that shaped this project — know them cold."),
);

const decisions = [
  ["Real catalog, synthetic transactions",
   "Pro: product identity and prices are real, so the project isn't pure fiction. Con: order timestamps are invented, so we can't claim to represent any real market. Honest middle ground: the distribution of baskets (sizes, qtys) comes from real /carts data."],
  ["FastAPI over Faker-only producer",
   "Pro: exposes a real HTTP + WebSocket surface external consumers can tap; makes the demo interactive via /trigger/*. Con: adds a web framework and an async loop to debug. Worth it for the demo ergonomics."],
  ["Kafka over Redis Streams",
   "Pro: replay from offset, partitioning, mature Spark connector. Con: heavier local footprint (Zookeeper + broker). Acceptable because it's the realistic choice at any production scale."],
  ["Spark over Flink / Kafka Streams",
   "Pro: Python-native, familiar to most data teams, great notebook story. Con: higher per-batch latency than Flink. Acceptable at minute granularity."],
  ["MySQL over Postgres or a warehouse",
   "Pro: easiest Docker setup, best Power BI DirectQuery driver support. Con: no columnar storage, so larger history windows would be slow. Would swap to BigQuery for production."],
  ["foreachBatch over multiple writeStreams",
   "Pro: atomic multi-sink per batch, lets us mix JDBC writes with raw SQL. Con: all writes serialize through the driver. At 10k orders/s we'd move some sinks back to writeStream with foreachPartition."],
  ["Staging-table upsert over MERGE statement",
   "Pro: works with MySQL 8's ON DUPLICATE KEY UPDATE; Spark JDBC can append. Con: requires a TRUNCATE each batch — a tiny window where staging is visible to other readers. Fine for an internal table."],
  ["Isolation Forest over Prophet / DeepAR",
   "Pro: trains in milliseconds on ~120 rows, no seasonality assumption. Con: ignores time-of-day effects. With more history we'd move to a seasonal naive baseline → STL → Prophet progression."],
  ["Config-as-data KPIs over code",
   "Pro: product can tune SLOs without a deploy. Con: no compile-time validation; a typo silently no-ops. Mitigation: evaluator validates the comparison enum on load."],
  ["DirectQuery over Import",
   "Pro: dashboards are as fresh as the database. Con: every visual is a live query — scaling Power BI requires caring about MySQL's query load. Fine at demo scale; in production we'd front it with a read replica."],
];

children.push(TwoColTable(decisions, "Decision", "Trade-off", [2800, 6560]));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===========================================================================
// 9. GLOSSARY
// ===========================================================================
children.push(
  H1("9. Glossary"),
  P("Terms that will come up in any interview about this project."),
);

const glossary = [
  ["Event time vs processing time", "Event time is when the event happened (order_timestamp); processing time is when the system handled it. Event-time windowing + watermarks correctly bucket late-arriving events."],
  ["Watermark", "A threshold in event time past which Spark ignores late data and finalizes windows. 'Watermark of 10 minutes' = data older than max(event_time) − 10 min is dropped."],
  ["Tumbling window", "Non-overlapping fixed-size time buckets. A 1-minute tumbling window puts each order in exactly one minute."],
  ["foreachBatch", "Spark Structured Streaming sink that gives you the micro-batch DataFrame and batch_id so you can write it anywhere, any way, transactionally."],
  ["Idempotency", "Running the same operation twice produces the same result. Critical for streaming, where retries and replays happen."],
  ["Exactly-once semantics", "Each event is effectively processed once. Structured Streaming achieves this with checkpointing + idempotent sinks."],
  ["Staging-table upsert", "Write-then-merge pattern: append raw rows to a staging table, then MERGE/UPSERT into the final table, then TRUNCATE staging."],
  ["Isolation Forest", "Unsupervised anomaly detection that isolates outliers via random tree splits. Low score = anomalous."],
  ["z-score", "(value − mean) / std. |z| > 3 is the conventional outlier threshold for roughly normal data."],
  ["SLO (Service Level Objective)", "A business-defined target (e.g., 'revenue per 5 minutes > $100'). Violating an SLO triggers an alert."],
  ["DirectQuery", "Power BI mode where each visual sends a live query to the data source on every refresh — no imported data."],
  ["Config-as-data", "Putting rules (KPI thresholds) in a database table instead of code, so they can be changed without a deploy."],
  ["Dedupe guard", "A WHERE NOT EXISTS clause preventing the same alert from being inserted more than once in a time window."],
  ["Schema evolution", "Changing the structure of events or tables over time without breaking existing producers/consumers."],
  ["Partition (Kafka)", "A log within a topic. Ordering is guaranteed within a partition, not across. Parallelism = number of partitions."],
  ["Consumer lag", "How far behind a consumer is from the latest message in a topic. The single most useful Kafka health metric."],
  ["Checkpoint (Spark)", "Durable record of progress so a streaming query can resume exactly where it stopped."],
  ["Micro-batch", "Spark Structured Streaming's execution model: process events in small batches (seconds) rather than per-event."],
];

children.push(TwoColTable(glossary, "Term", "Meaning", [2800, 6560]));

// ---------- CLOSING ----------
children.push(
  Spacer(),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 600 },
    children: [new TextRun({
      text: "If you can explain every term above and every trade-off in §8, you can defend this project in any interview.",
      italics: true, color: "666666",
    })],
  }),
);

// -------------------------------------------------------------------------
// build
// -------------------------------------------------------------------------

const doc = new Document({
  creator: "E-Commerce Monitor Project",
  title: "Real-Time E-Commerce Monitor - Complete Guide",
  description: "Interview-prep walkthrough",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, color: "1F3864", font: FONT },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "2E75B6", font: FONT },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "404040", font: FONT },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        ] },
      { reference: "numbers",
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        ] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },   // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({
          text: "Real-Time E-Commerce Monitor \u2014 Complete Guide",
          italics: true, size: 18, color: "888888",
        })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", size: 18, color: "888888" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888" }),
          new TextRun({ text: " of ", size: 18, color: "888888" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: "888888" }),
        ],
      })] }),
    },
    children,
  }],
});

const out = path.join(__dirname, "Project_Complete_Guide.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`wrote ${out} (${buf.length.toLocaleString()} bytes)`);
});
