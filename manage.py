#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
This file is created so the project structure exists before Python/Django are installed.
"""
import os
import sys


def main() -> None:

	# Purpose: Set the default settings module and delegate to Django's CLI.
	# Inputs: Command-line arguments from sys.argv.
	# Outputs: Executes Django management commands when Django is available.
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "college_portal.settings")
	try:
		from django.core.management import execute_from_command_line
	except Exception:
		# If Django isn't installed yet, provide a friendly message.
		print("Django is not installed yet. Install dependencies, then run: python manage.py migrate")
		return
	execute_from_command_line(sys.argv)


if __name__ == "__main__":
	main()



