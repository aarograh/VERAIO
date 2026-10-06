"""
Validation engine for VERAIn input parameters.

This module provides comprehensive validation functionality for VERA input parameters
including type checking, range validation, array size validation, and custom checks.
"""

from operator import __eq__, __ge__, __gt__, __le__, __lt__, __mod__, __ne__
import re
from typing import Dict, Any, List, Optional


class ValidationEngine:
    """
    Handles validation of input parameters based on Directory.yml check
    specifications
    """

    _operators = {
        "==": __eq__,
        "!=": __ne__,
        ">=": __ge__,
        ">": __gt__,
        "<=": __le__,
        "<": __lt__,
    }

    # This is a bit brittle because the ordering of >= and > matters
    # since ">" is inside ">="
    _operator_to_check = {
        "==": "is_eq",
        "eq": "is_eq",
        "!=": "is_neq",
        "ne": "is_neq",
        ">=": "is_geq",
        ">": "is_gt",
        "<=": "is_leq",
        "<": "is_lt",
    }

    def __init__(self):
        """Initialize the validation engine with built-in check functions"""
        self.check_functions = self._build_check_functions()

    def _build_check_functions(self) -> Dict[str, Any]:
        """Build dictionary of validation check functions"""

        def is_string(values):
            """Check if values are strings (any value is considered a string)"""
            return all(isinstance(v, str) or v is not None for v in values)

        def is_word(values):
            """Check if values are words (no whitespace in the middle)"""
            for v in values:
                if not isinstance(v, str):
                    return False
                # Check if there's whitespace in the value
                if " " in v or "\t" in v or "\n" in v:
                    return False
            return True

        def is_int(values):
            """Check if values are integers"""
            for v in values:
                try:
                    int(v)
                except (ValueError, TypeError):
                    return False
            return True

        def is_float(values):
            """Check if values are floats"""
            for v in values:
                try:
                    float(v)
                except (ValueError, TypeError):
                    return False
            return True

        def _operator_check(values, threshold, operator):
            """Generic operator check"""
            for v in values:
                try:
                    if not operator(float(v), float(threshold)):
                        return False
                except (ValueError, TypeError):
                    try:
                        if not operator(str(v), str(threshold)):
                            return False
                    except (ValueError, TypeError):
                        return False
            return True

        def is_geq(values, threshold):
            """Check if values are greater than or equal to threshold"""
            return _operator_check(values, threshold, __ge__)

        def is_gt(values, threshold):
            """Check if values are greater than threshold"""
            return _operator_check(values, threshold, __gt__)

        def is_leq(values, threshold):
            """Check if values are less than or equal to threshold"""
            return _operator_check(values, threshold, __le__)

        def is_lt(values, threshold):
            """Check if values are less than threshold"""
            return _operator_check(values, threshold, __lt__)

        def is_eq(values, threshold):
            """Check if values equal threshold"""
            return _operator_check(values, threshold, __eq__)

        def is_neq(values, threshold):
            """Check if values do not equal threshold"""
            return _operator_check(values, threshold, __ne__)

        def arraysize_check(values, operator, threshold):
            """Check array size against threshold using operator"""
            # If there's a '/' in the values, only count elements before it
            # for arraysize validation
            if "/" in values:
                slash_index = values.index("/")
                size = slash_index  # Count elements before the '/'
            else:
                size = len(values)

            if operator == "%":
                return size % threshold == 0
            if operator in self._operators:
                return self._operators[operator](size, threshold)
            return False

        def in_dictionary(values: List, valid_values: List):
            """Check if values are in the dictionary of valid values"""
            valid_set = set(str(v) for v in valid_values)
            return all(str(v) in valid_set for v in values)

        def not_in_dictionary(values: List, invalid_values: List):
            """Check if values are NOT in the dictionary of invalid values"""
            invalid_set = set(str(v) for v in invalid_values)
            return all(str(v) not in invalid_set for v in values)

        def is_increasing(values: List):
            """Check if values are increasing"""
            if len(values) <= 1:
                return True
            try:
                float_values = [float(v) for v in values]
                return all(float_values[i] <= float_values[i + 1] for i in range(len(float_values) - 1))
            except (ValueError, TypeError):
                return False

        def is_strictlyincreasing(values: List):
            """Check if values are strictly increasing"""
            if len(values) <= 1:
                return True
            try:
                float_values = [float(v) for v in values]
                return all(float_values[i] < float_values[i + 1] for i in range(len(float_values) - 1))
            except (ValueError, TypeError):
                return False

        def is_decreasing(values: List):
            """Check if values are decreasing"""
            if len(values) <= 1:
                return True
            try:
                float_values = [float(v) for v in values]
                return all(float_values[i] >= float_values[i + 1] for i in range(len(float_values) - 1))
            except (ValueError, TypeError):
                return False

        def is_strictlydecreasing(values: List):
            """Check if values are strictly decreasing"""
            if len(values) <= 1:
                return True
            try:
                float_values = [float(v) for v in values]
                return all(float_values[i] > float_values[i + 1] for i in range(len(float_values) - 1))
            except (ValueError, TypeError):
                return False

        def nth(values: List[str], check: str) -> bool:
            """Evaluate comparisons between nth elements like nth(0,())<=nth(1,())"""

            pattern = r"nth\((\d+),\(\)\)\s*([<>=!]+)\s*nth\((\d+),\(\)\)"
            match = re.match(pattern, check)

            if not match:
                return True

            left_index = int(match.group(1))
            operator = match.group(2)
            right_index = int(match.group(3))

            # Check bounds
            if left_index >= len(values) or right_index >= len(values):
                return False

            try:
                left_value = float(values[left_index])
                right_value = float(values[right_index])

                return ValidationEngine._operators[operator](left_value, right_value)
            except (ValueError, TypeError):
                return False

        return {
            "is_string": is_string,
            "is_word": is_word,
            "is_int": is_int,
            "is_float": is_float,
            "is_geq": is_geq,
            "is_gt": is_gt,
            "is_leq": is_leq,
            "is_lt": is_lt,
            "is_eq": is_eq,
            "is_neq": is_neq,
            "arraysize_check": arraysize_check,
            "in_dictionary": in_dictionary,
            "not_in_dictionary": not_in_dictionary,
            "is_increasing": is_increasing,
            "is_strictlyincreasing": is_strictlyincreasing,
            "is_decreasing": is_decreasing,
            "is_strictlydecreasing": is_strictlydecreasing,
            "nth": nth,
        }

    def _filter_value_tokens(self, values: List[str]) -> List[str]:
        """
        Filter out non-value tokens like '=' from parameter values.

        Args:
            values: Raw list of parameter tokens

        Returns:
            Filtered list containing only actual values
        """
        if not values:
            return values

        # Remove common non-value tokens
        filtered = []
        for value in values:
            # Skip equals signs and other assignment operators
            if value in ["=", "+=", "-=", "*=", "/=", "==", "!="]:
                continue

            # Skip block references like [STATE];
            if value.startswith("[") and value.endswith("];"):
                continue

            # Remove trailing punctuation like semicolons and commas
            cleaned_value = value.rstrip(";,")
            if cleaned_value:  # Only add non-empty values
                filtered.append(cleaned_value)

        return filtered

    # Longest value list echoed in an error message; a map can hold hundreds.
    _MAX_ECHOED_VALUES = 12

    def _describe_values(self, values: List[str], block: Optional[str] = None) -> str:
        """Where a parameter's values came from, for an error message"""
        shown = [str(v) for v in values[: self._MAX_ECHOED_VALUES]]
        text = " ".join(shown)
        if len(values) > self._MAX_ECHOED_VALUES:
            text += f" ... ({len(values)} values in all)"
        label = "value" if len(values) == 1 else "values"
        where = f"in [{block}], " if block else ""
        return f"{where}{label}: {text}"

    def validate_parameter(
        self, param_name: str, values: List[str], checks: List[str], block: Optional[str] = None
    ) -> List[str]:
        """
        Validate parameter values against all specified checks

        Args:
            param_name: Name of parameter being validated
            values: List of string values from input
            checks: List of check specifications
            block: Name of the block the parameter was read from, echoed in
                error messages (optional)

        Returns:
            List of validation error messages (empty if all valid).  Each
            message echoes the values that were checked: an unrecognized
            keyword is read as more values of the keyword before it, so the
            values are what show where the input went wrong.
        """
        errors = []

        # Filter out '=' tokens and other non-value tokens before validation
        filtered_values = self._filter_value_tokens(values)

        for check in checks:
            try:
                if not self._evaluate_check(filtered_values, check):
                    errors.append(
                        f"Parameter '{param_name}' failed validation: {check} "
                        f"({self._describe_values(filtered_values, block)})"
                    )
            # pylint: disable=broad-exception-caught
            except Exception as e:
                errors.append(
                    f"Parameter '{param_name}' validation error for check '{check}': {e} "
                    f"({self._describe_values(filtered_values, block)})"
                )

        return errors

    def _evaluate_stride(self, stride_str: str, value: List[Any]) -> List[Any]:
        """Evaluate stride string and return selected values"""
        match = re.search(r"stride\((\d+),(\d+),\(\)\)", stride_str)
        if not match:
            raise ValueError("Invalid stride format")

        start = int(match.group(1))
        step = int(match.group(2))

        return [value[i] for i in range(start, len(value), step) if i < len(value)]

    # pylint: disable=too-many-statements
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    def _evaluate_check(self, values: List[str], check: str) -> bool:
        """Evaluate a single check specification"""

        # Remove surrounding parentheses
        while check.startswith("(") and check.endswith(")"):
            check = check[1:-1].strip()

        # Handle logical AND operations (&&)
        if "&&" in check:
            and_parts = check.split("&&")
            return all(self._evaluate_check(values, part.strip()) for part in and_parts)

        # Handle logical OR operations (||)
        if "||" in check:
            or_parts = check.split("||")
            return any(self._evaluate_check(values, part.strip()) for part in or_parts)

        # Handle checks on only parts of the data
        if "stride" in check:
            # Remove stride pattern and any preceding comma
            no_stride_check = re.sub(r",?\s*stride\(\d+,\d+,\(\)\)", "", check).strip()
            stride_values = self._evaluate_stride(check, values)
            return self._evaluate_check(stride_values, no_stride_check)
        if "odd([])" in check:
            no_odd_check = re.sub(r",?\s*odd\(\[\]\)", "", check).strip()
            odd_values = [values[i] for i in range(len(values)) if i % 2 == 1]
            return self._evaluate_check(odd_values, no_odd_check)
        if "even([])" in check:
            no_even_check = re.sub(r",?\s*even\(\[\]\)", "", check).strip()
            even_values = [values[i] for i in range(len(values)) if i % 2 == 0]
            return self._evaluate_check(even_values, no_even_check)
        if "nth(" in check:
            return self.check_functions["nth"](values, check)

        # Handle fall(sub{...},...) patterns
        if check.startswith("fall(sub{"):
            sub_check = check.split("fall(sub{")[-1].split("}")[0].strip()
            sub_check = "".join(sub_check.split("shift,")).strip()
            return all(self._evaluate_check([v], sub_check) for v in values)

        check_func_args = {"values": values}
        check_name = None

        # Handle arraysize checks
        if check.startswith("arraysize()"):
            check_name = "arraysize"
            # Handle modulo operations like arraysize()%3==0
            if "%" in check:
                # Parse modulo operations: arraysize()%N==M
                for op, op_func in self._operators.items():
                    if op in check:
                        parts = check.split(op)
                        if len(parts) == 2:
                            left_part = parts[0].strip()  # e.g., "arraysize()%3"
                            right_part = parts[1].strip()  # e.g., "0"

                            # Extract modulo value from left part
                            if "%" in left_part:
                                mod_parts = left_part.split("%")
                                if len(mod_parts) == 2 and mod_parts[0] == "arraysize()":
                                    try:
                                        mod_value = int(mod_parts[1])
                                        threshold = int(right_part)

                                        # Calculate array_size % mod_value and
                                        # compare with threshold
                                        array_size = len(values)
                                        if "/" in values:
                                            array_size = values.index("/")

                                        mod_result = array_size % mod_value

                                        return op_func(mod_result, threshold)
                                    except ValueError:
                                        return False
                        break
            else:
                # Handle regular arraysize operations without modulo
                for op in self._operators:
                    if op in check:
                        parts = check.split(op)
                        if len(parts) == 2:
                            threshold_str = parts[1].strip()
                            try:
                                threshold = int(threshold_str)
                                return self.check_functions["arraysize_check"](values, op, threshold)
                            except ValueError:
                                return False

        # Handle in_dictionary patterns
        if check.startswith("in_dictionary(") and check.endswith(")"):
            check_name = "in_dictionary"
            content = check[14:-1]  # Remove 'in_dictionary(' and ')'
            check_func_args["valid_values"] = [v.strip().strip("\"'") for v in content.split(",")]
        if check.startswith("in_dictionary()"):
            check_name = "in_dictionary"
            content = check[16:]  # Remove 'in_dictionary() '
            check_func_args["valid_values"] = [v.strip().strip("\"'") for v in content.split()]
        if check.startswith("not_in_dictionary(") and check.endswith(")"):
            check_name = "not_in_dictionary"
            content = check[18:-1]  # Remove 'not_in_dictionary(' and ')'
            check_func_args["invalid_values"] = [v.strip().strip("\"'") for v in content.split(",")]
        if check.startswith("not_in_dictionary()"):
            check_name = "not_in_dictionary"
            content = check[20:]  # Remove 'not_in_dictionary() '
            check_func_args["invalid_values"] = [v.strip().strip("\"'") for v in content.split()]

        # Handle string comparisons
        if ("eq'" in check or 'eq"' in check) and check_name is None:
            check_name = "is_eq"
            check_func_args["threshold"] = check.split("eq")[-1].strip()[1:-1]  # type: ignore
        if ("ne'" in check or 'ne"' in check) and check_name is None:
            check_name = "is_neq"
            check_func_args["threshold"] = check.split("ne")[-1].strip()[1:-1]  # type: ignore

        # Handle operators like >=, <=, ==, !=, >, <
        for op in self._operators:
            if op in check:
                parts = check.split(op)
                lhs = parts[1] not in ("", "(shift)")
                if lhs:
                    check_func_args["threshold"] = float(parts[1])  # type: ignore
                else:
                    assert len(check_func_args["values"]) == 1
                    check_func_args["values"], check_func_args["threshold"] = (  # type: ignore
                        [float(parts[0])],
                        check_func_args["values"][0],
                    )
                check_name = self._operator_to_check[op]
                break

        # Simple checks that weren't identified yet
        if check_name is None:
            check_name = check.split("(")[0]

        # Make sure the threshold is set for simple checks that didn't use operator symbols
        if check_name in ("is_eq", "is_geq", "is_gt", "is_leq", "is_lt") and "threshold" not in check_func_args:
            threshold_str = check.split("()")[-1].strip() if "()" in check else check.split("(")[-1].strip(")")
            try:
                check_func_args["threshold"] = float(threshold_str)  # type: ignore
            except ValueError:
                check_func_args["threshold"] = threshold_str  # type: ignore

        # Evaluate the check
        return self.check_functions[check_name](**check_func_args)
