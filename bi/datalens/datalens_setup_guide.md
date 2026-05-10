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
- `datalens_propensity_deciles.csv`, если уже обучена модель вероятности покупки

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

## 3. Датасеты

### Датасет `datalens_funnel_daily`

Источник: `data/marts/datalens_funnel_daily.csv`

Измерения:

- `event_date`
- `category_code`
- `brand`

Показатели:

- `views_cnt`
- `carts_cnt`
- `purchases_cnt`
- `revenue`

Вычисляемые поля:

- `Конверсия просмотра в корзину` = `SUM([carts_cnt]) / SUM([views_cnt])`
- `Конверсия корзины в покупку` = `SUM([purchases_cnt]) / SUM([carts_cnt])`
- `Конверсия просмотра в покупку` = `SUM([purchases_cnt]) / SUM([views_cnt])`
- `Drop-off корзины` = `1 - SUM([purchases_cnt]) / SUM([carts_cnt])`

### Датасет `datalens_retention`

Источник: `data/marts/datalens_retention.csv`

Измерения:

- `cohort_month`
- `order_month`
- `months_since_first_purchase`

Показатели:

- `active_users`
- `cohort_size`
- `retention_rate`

Вычисляемые поля:

- `Retention rate` = `AVG([retention_rate])`

### Датасет `datalens_product_conversion`

Источник: `data/marts/datalens_product_conversion.csv`

Измерения:

- `product_id`
- `category_code`
- `brand`

Показатели:

- `views_cnt`
- `carts_cnt`
- `purchases_cnt`
- `revenue`
- `conversion_rate`

Вычисляемые поля:

- `Конверсия товара` = `SUM([purchases_cnt]) / SUM([views_cnt])`

### Датасет `datalens_sessions_summary`

Источник: `data/marts/datalens_sessions_summary.csv`

Измерения:

- `session_date`
- `session_depth_segment`

Показатели:

- `sessions_cnt`
- `purchase_sessions_cnt`
- `cart_sessions_cnt`
- `abandoned_cart_sessions_cnt`
- `revenue`
- `avg_session_duration_minutes`
- `avg_events_cnt`

Вычисляемые поля:

- `Конверсия сессии в покупку` = `SUM([purchase_sessions_cnt]) / SUM([sessions_cnt])`
- `Доля брошенных корзин` = `SUM([abandoned_cart_sessions_cnt]) / SUM([cart_sessions_cnt])`
- `GMV` = `SUM([revenue])`

### Датасет `datalens_propensity_deciles`

Источник: `data/marts/datalens_propensity_deciles.csv`

Создайте dataset только если файл существует. Для модели используется агрегат по децилям, а не полный session-level файл. Это уменьшает размер загрузки и оставляет показатели, нужные для BI-графика.

Измерения:

- `score_decile`

Показатели:

- `sessions_cnt`
- `purchases_cnt`
- `purchase_rate`
- `avg_score`
- `revenue`, если колонка есть
- `revenue_per_session`, если колонка есть

Вычисляемые поля:

- `Доля покупок` = `AVG([purchase_rate])`
- `Средний скоринг модели` = `AVG([avg_score])`
- `Сессии` = `SUM([sessions_cnt])`

## 4. Чарты

### KPI-карточки

Используйте datasets:

- `datalens_funnel_daily` для purchase conversion rate, cart-to-purchase rate и GMV;
- `datalens_sessions_summary` для abandoned cart share.

Чарты:

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

### Таблица проблемных категорий с высоким drop-off

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

Источник: `datalens_propensity_deciles`.

- X: `score_decile`
- Y: `Доля покупок`
- Дополнительная мера: `Средний скоринг модели`

Если файла `datalens_propensity_deciles.csv` нет, сначала обучите модель и повторите экспорт:

```powershell
python scripts/train_propensity_model.py
python scripts/export_for_datalens.py
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

## 7. Скриншоты

После ручной сборки dashboard положите главный скриншот в:

- `assets/dashboard_full_view.png`

Если нужен дополнительный скриншот KPI и воронки, положите его в:

- `assets/dashboard_kpi_funnel_view.png`
