# Спецификация dashboard

Dashboard в Yandex DataLens состоит из управленческого и аналитического блоков. Все элементы строятся на CSV-экспортах из `data/marts/`.

## Блок KPI

Цель блока — дать быстрый обзор состояния воронки и продаж.

Показатели:

- GMV;
- конверсия в покупку;
- конверсия из корзины в покупку;
- доля брошенных корзин;
- количество покупок;
- количество сессий.

Рекомендуемые источники:

- `datalens_funnel_daily.csv` для GMV и событийной конверсии;
- `datalens_sessions_summary.csv` для сессионных показателей и abandoned cart share.

## Блок funnel и category conversion

Цель блока — показать путь `view -> cart -> purchase` и различия между категориями и брендами.

Чарты:

- funnel chart `view -> cart -> purchase`;
- bar chart конверсии по `category_code`;
- bar chart или таблица по `brand`;
- таблица категорий с высоким traffic и низкой conversion.

Основные поля:

- `event_date`;
- `category_code`;
- `brand`;
- `views_cnt`;
- `carts_cnt`;
- `purchases_cnt`;
- `revenue`.

## Блок retention

Цель блока — показать, как меняется повторная активность покупательских когорт.

Чарты:

- cohort retention heatmap;
- retention curve по номеру месяца после первой покупки.

Источник:

- `datalens_retention.csv`

Основные поля:

- `cohort_month`;
- `order_month`;
- `months_since_first_purchase`;
- `active_users`;
- `cohort_size`;
- `retention_rate`.

## Блок propensity scoring

Цель блока — показать качество ранжирования сессий по вероятности покупки.

Для BI используется агрегат по децилям, а не полный session-level файл.

Источник:

- `datalens_propensity_deciles.csv`

Чарты:

- decile chart по `score_decile`;
- bar chart доли покупок по децилям;
- таблица с количеством сессий, покупок, purchase rate и avg score.

Основные поля:

- `score_decile`;
- `sessions_cnt`;
- `purchases_cnt`;
- `purchase_rate`;
- `avg_score`.

## Блок product/category drop-off

Цель блока — найти товары, категории и бренды с высоким интересом, но слабой покупкой.

Источники:

- `datalens_product_conversion.csv`;
- `datalens_funnel_daily.csv`.

Чарты:

- product conversion table;
- таблица проблемных категорий;
- таблица проблемных брендов;
- scatter session depth vs conversion.

Основные поля:

- `product_id`;
- `category_code`;
- `brand`;
- `views_cnt`;
- `carts_cnt`;
- `purchases_cnt`;
- `conversion_rate`;
- `revenue`.

## Screenshots

Главный скриншот dashboard для README:

```text
assets/dashboard_full_view.png
```

Дополнительный скриншот KPI и воронки:

```text
assets/dashboard_kpi_funnel_view.png
```
