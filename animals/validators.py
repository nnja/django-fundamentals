"""The phone number rule for adoption applications.

A US number of ten digits, with no country code, written as 555-010-2000,
(555) 010-2000, 555 010 2000, or 5550102000. For numbers from any country,
a project would use django-phonenumber-field, which validates and stores
them with Google's libphonenumber.
"""

from django.core.validators import RegexValidator

# [0-9], not \d: in Python, \d also matches digits from other scripts.
# \Z, not $: $ also matches just before a trailing newline.
validate_phone = RegexValidator(
    regex=r"^(\([0-9]{3}\)|[0-9]{3})[ -]?[0-9]{3}[ -]?[0-9]{4}\Z",
    message="Enter a 10-digit US phone number, like 555-010-2000.",
)
