#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from automdjango.tests.test_examine import Test_examine, driver


def main(driver):
    Test_examine().test_main_program(driver)

if __name__ == '__main__':
    m_instance_driver = Test_examine().drivernation()
    main(m_instance_driver)
