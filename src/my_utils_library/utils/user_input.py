# MODULE DETAILS ----------------------------------------------------------------------------------------------------------
# user_input.py
# Created 7/20/23 - 3:12 PM UK Time (London) by carlogtt
# ----------------------------------------------------------------------------------------------------------------------

"""
This module ...
"""

# IMPORTS --------------------------------------------------------------------------------------------------------------
# Importing required libraries and modules for the application.

# Standard Library Imports ---------------------------------------------------------------------------------------------
import logging

# END IMPORTS ----------------------------------------------------------------------------------------------------------


# List of public names in the module
# __all__ = [...]

# Setting up logger for current module
module_logger = logging.getLogger(__name__)


def get_user_input_and_validate_int(question: str = "Enter a number: ") -> int:
    """
    Request the user for an int
    question = "question as a str"
    """
    while True:
        input_value = input(question)

        try:
            int(input_value)

        except ValueError:
            continue

        else:
            return int(input_value)


def get_user_input_confirmation_y_n(question: str = "Continue: (y/n): ", true: str = "y", false: str = "n") -> bool:
    """
    Request the user for a confirmation to continue
    question = "question as a str"
    true = "character to be used as continue"
    false = "character to be used to stop"
    """

    while True:
        input_value = input(question)

        if true.isalpha() and false.isalpha():
            if true.islower() and false.islower():
                if input_value[0].lower() == true or input_value[0].lower() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.isupper() and false.isupper():
                if input_value[0].upper() == true or input_value[0].upper() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.islower() and false.isupper():
                if input_value[0].lower() == true or input_value[0].upper() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.isupper() and false.islower():
                if input_value[0].upper() == true or input_value[0].lower() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

        elif true.isalpha():
            if true.islower():
                if input_value[0].lower() == true or input_value[0] == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif true.isupper():
                if input_value[0].upper() == true or input_value[0] == false:
                    if input_value == true:
                        return True

                    else:
                        return False

        elif false.isalpha():
            if false.islower():
                if input_value[0] == true or input_value[0].lower() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

            elif false.isupper():
                if input_value[0] == true or input_value[0].upper() == false:
                    if input_value == true:
                        return True

                    else:
                        return False

        else:
            if input_value[0] == true or input_value[0] == false:
                if input_value == true:
                    return True

                else:
                    return False


if __name__ == '__main__':
    pass
