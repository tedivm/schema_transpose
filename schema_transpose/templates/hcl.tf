variable "{{name}}" {
  type = {{ type -}}
  {% if has_default %}
  default = {{ default }}
  {%- endif -%}
  {% if description %}
  description = "{{ description }}"
  {%- endif %}
  {%- if sensitive %}
  sensitive = true
  {%- endif %}
  {%- for rule in validation_rules %}
  validation {
    # {{ rule.comment }}
    condition     = {{ rule.condition }}
    error_message = "{{ rule.message }}"
  }
  {%- endfor %}
}
