"""
A package for automating interactions with the SESS university system.

This package provides functions to log in, navigate the registration pages,
and attempt to register for a predefined list of courses.
"""

# Import functions from the module to make them directly accessible at the package level.
from .sess_client import (
    log_in,
    navigate_to_registration_page,
    get_available_courses,
    handle_system_messages,
    attempt_course_registration,
    check_unavailable_course_reasons
)

# Define the public API of the package. When a user writes `from automation import *`,
# only the names listed in `__all__` will be imported. This also serves as
# clear documentation for the package's intended interface.
__all__ = [
    'log_in',
    'navigate_to_registration_page',
    'get_available_courses',
    'handle_system_messages',
    'attempt_course_registration',
    'check_unavailable_course_reasons'
]