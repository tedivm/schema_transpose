# Pydantic to Terraform

This library converts Pydantic Models into Terraform Variables.


## Usage

This needs to be installed in the same virtual environment as the Models that it is converting. Once installed a CLI tool, `py2tf`, will be available in the environment.

For example, to generate a variables file for the RDS ParameterValidation class-

```shell
robert@Roberts-MacBook-Pro terraform-aws-core % py2tf modules.rds.validation.parameters:ParameterValidation
```

The command will output the following to stdout:

```hcl
variable "type" {
  type = string
  default = null
}

variable "pit_identifier" {
  type = string
  default = null
}

variable "tags" {
  type = map(any)
  default = {}
}

variable "name" {
  type = string
  validation {
    # Automatically Generated from Rule: minlength
    condition     = length(var.name) >= 1
    error_message = "Field should not be less than 1 characters"
  }
  validation {
    # Automatically Generated from Rule: maxlength
    condition     = length(var.name) <= 63
    error_message = "Field should not be larger than 63 characters"
  }
  validation {
    # Automatically Generated from Rule: pattern
    condition     = length(regexall("^(?!.*--)[a-zA-Z][A-Za-z0-9.-]+(?<!-)$", var.name)) > 0
    error_message = "Field does not match regex pattern ^(?!.*--)[a-zA-Z][A-Za-z0-9.-]+(?<!-)$"
  }
}

variable "vpc_name" {
  type = string
}

variable "engine" {
  type = string
  validation {
    # Automatically Generated from Rule: minlength
    condition     = length(var.engine) >= 1
    error_message = "Field should not be less than 1 characters"
  }
}

variable "engine_version" {
  type = string
  validation {
    # Automatically Generated from Rule: minlength
    condition     = length(var.engine_version) >= 1
    error_message = "Field should not be less than 1 characters"
  }
}

variable "is_public" {
  type = bool
  default = false
}
```


## Next Steps

At the moment this does not generate validation rules (min/max length, regex, etc).
