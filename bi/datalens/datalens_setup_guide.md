# Настройка dashboard в Yandex DataLens

Этот документ описывает ручную сборку dashboard в Yandex DataLens на CSV-экспортах из проекта. Автоматическое создание dashboard не используется.

## 1. Подготовить CSV-файлы

Сначала выполните локально:

```powershell
python scripts/run_etl.py
python scripts/build_marts.py
python scripts/train_propensity_model.py
python scripts/export_for_datalens.py
```

После экспорта в `data/marts/` должны появиться файлы:

- `datalens_funnel_daily.csv`
- `datalens_retention.csv`
- `datalens_product_conversion.csv`
- `datalens_sessions_summary.csv`
- `datalens_propensity_scores.csv`, если уже обучена модель вероятности покупки

CSV сохраняются в UTF-8.

## 2. Подключить CSV к Yandex DataLens

1. Откройте Yandex DataLens.
2. Создайте новое подключение типа `Файл`.
3. Загрузите нужный CSV из `data/marts/`.
4. Проверьте типы колонок:
   - даты должны быть типом `Дата` или `Дата и время`;
   - счетчики и выручка должны быть числовыми;
   - категории, бренды и дециль скоринга должны быть строками.
5. Для каждого CSV создайте отдельный dataset.

## 3. Datasets

### Dataset `datalens_funnel_daily`

Источник: `data/marts/datalens_funnel_daily.csv`

Dimensions:

- `event_date`
- `category_code`
- `brand`

Measures:

- `views_cnt`
- `carts_cnt`
- `purchases_cnt`
- `revenue`

Calculated fields:

- `Конверсия просмотра в корзину` = `SUM([carts_cnt]) / SUM([views_cnt])`
- `Конверсия корзины в покупку` = `SUM([purchases_cnt]) / SUM([carts_cnt])`
- `Конверсия просмотра в покупку` = `SUM([purchases_cnt]) / SUM([views_cnt])`
- `Drop-off корзины` = `1 - SUM([purchases_cnt]) / SUM([carts_cnt])`

### Dataset `datalens_retention`

Источник: `data/marts/datalens_retention.csv`

Dimensions:

- `cohort_month`
- `order_month`
- `months_since_first_purchase`

Measures:

- `active_users`
- `cohort_size`
- `retention_rate`

Calculated fields:

- `Retention rate` = `AVG([retention_rate])`

### Dataset `datalens_product_conversion`

Источник: `data/marts/datalens_product_conversion.csv`

Dimensions:

- `product_id`
- `category_code`
- `brand`

Measures:

- `views_cnt`
- `carts_cnt`
- `purchases_cnt`
- `revenue`
- `conversion_rate`

Calculated fields:

- `Конверсия товара` = `SUM([purchases_cnt]) / SUM([views_cnt])`

### Dataset `datalens_sessions_summary`

Источник: `data/marts/datalens_sessions_summary.csv`

Dimensions:

- `session_date`
- `session_depth_segment`

Measures:

- `sessions_cnt`
- `purchase_sessions_cnt`
- `cart_sessions_cnt`
- `abandoned_cart_sessions_cnt`
- `revenue`
- `avg_session_duration_minutes`
- `avg_events_cnt`

Calculated fields:

- `Конверсия сессии в покупку` = `SUM([purchase_sessions_cnt]) / SUM([sessions_cnt])`
- `Доля брошенных корзин` = `SUM([abandoned_cart_sessions_cnt]) / SUM([cart_sessions_cnt])`
- `GMV` = `SUM([revenue])`

### Dataset `datalens_propensity_scores`

Источник: `data/marts/datalens_propensity_scores.csv`

Создайте dataset только если файл существует.

Dimensions:

- `score_decile`
- `session_start`

Measures:

- `purchase_flag`
- `baseline_score`
- `model_score`

Calculated fields:

- `Доля покупок` = `AVG([purchase_flag])`
- `Средний скоринг модели` = `AVG([model_score])`
- `Сессии` = `COUNT([session_id])`

## 4. Charts

### KPI cards

Используйте datasets:

- `datalens_funnel_daily` для purchase conversion rate, cart-to-purchase rate и GMV;
- `datalens_sessions_summary` для abandoned cart share.

Charts:

- KPI `Конверсия просмотра в покупку`
- KPI `Конверсия корзины в покупку`
- KPI `GMV`
- KPI `Доля брошенных корзин`

### Funnel view -> cart -> purchase

Источник: `datalens_funnel_daily`.

Соберите funnel chart или bar chart с этапами:

- `Просмотры` = `SUM([views_cnt])`
- `Корзины` = `SUM([carts_cnt])`
- `Покупки` = `SUM([purchases_cnt])`

### Bar chart по category_code

Источник: `datalens_funnel_daily`.

- Dimension: `category_code`
- Measure: `Конверсия просмотра в покупку`
- Дополнительная мера: `SUM([views_cnt])`
- Сортировка: по просмотрам или по конверсии

### Table проблемных категорий с высоким drop-off

Источник: `datalens_funnel_daily`.

Поля:

- `category_code`
- `SUM([views_cnt])`
- `SUM([carts_cnt])`
- `SUM([purchases_cnt])`
- `Конверсия просмотра в покупку`
- `Drop-off корзины`

Рекомендуемый фильтр: показывать только категории с достаточным количеством просмотров.

### Cohort retention heatmap

Источник: `datalens_retention`.

- Rows: `cohort_month`
- Columns: `months_since_first_purchase`
- Color: `Retention rate`

### Retention curve

Источник: `datalens_retention`.

- X: `months_since_first_purchase`
- Y: `Retention rate`

### Product conversion table

Источник: `datalens_product_conversion`.

Поля:

- `product_id`
- `category_code`
- `brand`
- `views_cnt`
- `carts_cnt`
- `purchases_cnt`
- `revenue`
- `conversion_rate`

### Scatter session depth vs conversion

Источник: `datalens_sessions_summary`.

- X: `avg_events_cnt`
- Y: `Конверсия сессии в покупку`
- Size: `SUM([sessions_cnt])`
- Color: `session_depth_segment`

### Decile chart по модели вероятности покупки

Источник: `datalens_propensity_scores`.

- X: `score_decile`
- Y: `Доля покупок`
- Дополнительная мера: `Средний скоринг модели`

Если файла `datalens_propensity_scores.csv` нет, сначала обучите модель командой:

```powershell
python scripts/train_propensity_model.py
```

## 5. Filters

Добавьте общие фильтры:

- `event_date` или `session_date`;
- `category_code`;
- `brand`;
- `score_decile`, если используется модель вероятности покупки.

## 6. Dashboard-страницы

### Страница 1. Управленческий обзор

Состав:

- KPI: purchase conversion rate;
- KPI: cart-to-purchase rate;
- KPI: GMV;
- KPI: abandoned cart share;
- funnel `view -> cart -> purchase`;
- bar chart по `category_code`;
- table проблемных категорий с высоким drop-off.

### Страница 2. Аналитический обзор

Состав:

- cohort retention heatmap;
- retention curve;
- product conversion table;
- category и brand filters;
- date filter;
- decile chart по модели вероятности покупки.

## 7. Screenshots

После ручной сборки dashboard положите screenshots в `assets/`:

- `dashboard_page_1_overview.png`
- `dashboard_page_2_analytics.png`
- `funnel_chart.png`
- `cohort_heatmap.png`
- `propensity_decile_chart.png`
