{% if description %}
# {{ description }}
{%- endif -%}
{% if has_default %}
{{name}} = {{ default }}
{%- else %}
{{name}} = FILL_THIS_IN
{%- endif %}
