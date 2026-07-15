# Template tags (generated)

Public callables discovered under `boxes.templatetags`.

## `boxes.templatetags.custom_filters`

General template filters and tags for tables, charts, and invoices.

### `card_brand_display(brand)`

Human label for a card brand code.

### `chart_is_selected(context, freq)`

Bootstrap button class for selected chart frequency.

### `chart_tab_is_selected(context, freq)`

Nav link class for active chart frequency tab.

### `data_tab_is_selected(context, chart)`

Nav link class for active data tab.

### `get_item(dictionary, key)`

Dictionary lookup filter; formats price and datetimes for display (or Unknown default).

### `get_item_pdf(dictionary, key)`

Dictionary lookup formatted for PDF (localized timestamps).

### `invoice_state_display(state)`

Human label for invoice PaymentIntent state int.

### `is_timestamp(dictionary, key)`

Return True if dictionary[key] is a datetime.

### `query_string(context, per_page=None)`

Build pagination query string preserving q/filter/frequency/chart/per_page.

## `boxes.templatetags.customer_filters`

Customer-portal template helpers for cards and money formatting.

### `format_negative(value)`

Format number as currency; negatives as ``$(x.xx)``.

### `get_card_logo(brand)`

Font Awesome class string for a payment brand.

### `get_card_number(card_type, last_four)`

Masked card number display for brand + last four.
