# Template tags (generated)

Public callables discovered under `boxes.templatetags`.

## `boxes.templatetags.custom_filters`

Compatibility re-export of dict/nav/payment filters.

Prefer loading the focused modules in templates::

    {% load dict_filters %}
    {% load nav_filters %}
    {% load payment_filters %}

Filter and tag *names* remain stable across the split.

## `boxes.templatetags.customer_filters`

Customer-portal template helpers for cards and money formatting.

### `format_negative(value)`

Format number as currency; negatives as ``$(x.xx)``.

### `get_card_logo(brand)`

Font Awesome class string for a payment brand.

### `get_card_number(card_type, last_four)`

Masked card number display for brand + last four.

## `boxes.templatetags.dict_filters`

Dictionary lookup template filters for tables and PDFs.

### `get_item(dictionary, key)`

Dictionary lookup filter; formats price and datetimes for display (or Unknown default).

### `get_item_or_unknown(dictionary, key)`

Dictionary lookup filter; formats price and datetimes for display (or Unknown default).

### `get_item_pdf(dictionary, key)`

Dictionary lookup formatted for PDF (localized timestamps).

### `is_timestamp(dictionary, key)`

Return True if dictionary[key] is a datetime.

## `boxes.templatetags.nav_filters`

Navigation and pagination template tags for reports and lists.

### `chart_is_selected(context, freq)`

Bootstrap button class for selected chart frequency.

### `chart_tab_is_selected(context, freq)`

Nav link class for active chart frequency tab.

### `data_tab_is_selected(context, chart)`

Nav link class for active data tab.

### `query_string(context, per_page=None)`

Build pagination query string preserving q/filter/frequency/chart/per_page.

## `boxes.templatetags.payment_filters`

Payment and invoice display template tags.

### `card_brand_display(brand)`

Human label for a card brand code.

### `invoice_state_display(state)`

Human label for invoice PaymentIntent state int.
