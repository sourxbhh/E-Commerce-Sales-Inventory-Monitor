# Data directory

**Nothing in this folder is committed to git.** See `.gitignore`.

## Layout

```
data/
├── raw/         # Olist CSVs straight from Kaggle (9 files, ~120 MB)
└── processed/   # Partitioned Parquet output of ingestion/olist_to_parquet.py
```

## Getting the Olist dataset

Source: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — ~100k orders from Sept 2016 to Oct 2018.

### Option A — Manual download (simplest)

1. Download the ZIP from the Kaggle page.
2. Extract into `data/raw/` so it looks like:

   ```
   data/raw/
       olist_customers_dataset.csv
       olist_geolocation_dataset.csv
       olist_order_items_dataset.csv
       olist_order_payments_dataset.csv
       olist_order_reviews_dataset.csv
       olist_orders_dataset.csv
       olist_products_dataset.csv
       olist_sellers_dataset.csv
       product_category_name_translation.csv
   ```

### Option B — Kaggle API

```powershell
pip install kaggle
# Put kaggle.json at $env:USERPROFILE\.kaggle\kaggle.json
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

## Table reference

| Table                                | Rows    | Notes                                    |
| ------------------------------------ | ------- | ---------------------------------------- |
| `olist_orders_dataset`               | ~99 k   | Fact-ish; partition by purchase month    |
| `olist_order_items_dataset`          | ~112 k  | One row per item in an order             |
| `olist_order_payments_dataset`       | ~104 k  | Multiple payment methods per order ok    |
| `olist_order_reviews_dataset`        | ~99 k   | Partition by review_creation_date month  |
| `olist_customers_dataset`            | ~99 k   | Dimension                                |
| `olist_products_dataset`             | ~33 k   | Dimension                                |
| `olist_sellers_dataset`              | ~3 k    | Dimension                                |
| `olist_geolocation_dataset`          | ~1 M    | Zip → lat/lng lookup                     |
| `product_category_name_translation`  | ~71     | Loaded as a dbt seed, not Parquet        |
