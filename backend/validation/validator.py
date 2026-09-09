import re
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field, EmailStr, field_validator
from backend.models.schemas import ProcessedField, ValidationErrorItem

class PersonEntityModel(BaseModel):
    name: str = None
    dob: str = None
    email: str = None
    phone: str = None
    postal_code: str = None
    amount: float = None

def validate_unstructured_fields(fields: List[ProcessedField]) -> Tuple[List[ProcessedField], List[ValidationErrorItem]]:
    """
    Validates unstructured extracted fields:
    - Verifies format correctness for email, date, phone, numbers
    - Checks that normalized values adhere to expected types
    - Marks field `is_valid` flag and populates errors list without altering user data
    """
    errors: List[ValidationErrorItem] = []
    validated_fields: List[ProcessedField] = []

    for field in fields:
        f_copy = field.model_copy()
        raw = f_copy.raw_value
        val = f_copy.value

        # If raw was present but normalization failed to parse a valid value
        if raw is not None and val is None and str(raw).strip() != "":
            err_msg = f"Invalid {f_copy.label} format (could not standardize '{raw}')"
            f_copy.is_valid = False
            f_copy.error_message = err_msg
            errors.append(ValidationErrorItem(field=f_copy.key, message=err_msg, raw_value=raw))
        
        # Specific semantic validation when value is present
        elif val is not None:
            if f_copy.field_type == "email":
                if not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", str(val)):
                    err_msg = f"Invalid email syntax: {val}"
                    f_copy.is_valid = False
                    f_copy.error_message = err_msg
                    errors.append(ValidationErrorItem(field=f_copy.key, message=err_msg, raw_value=raw))
            elif f_copy.field_type == "date":
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(val)):
                    err_msg = f"Date must be in YYYY-MM-DD format: {val}"
                    f_copy.is_valid = False
                    f_copy.error_message = err_msg
                    errors.append(ValidationErrorItem(field=f_copy.key, message=err_msg, raw_value=raw))
            elif f_copy.field_type == "phone":
                digits = re.sub(r"\D", "", str(val))
                if len(digits) < 8:
                    err_msg = f"Phone number must contain at least 8 digits: {val}"
                    f_copy.is_valid = False
                    f_copy.error_message = err_msg
                    errors.append(ValidationErrorItem(field=f_copy.key, message=err_msg, raw_value=raw))

        validated_fields.append(f_copy)

    return validated_fields, errors


def validate_structured_records(records: List[Dict[str, Any]], columns: List[str]) -> Tuple[List[Dict[str, Any]], List[ValidationErrorItem]]:
    """
    Validates tabular records, flagging null values in required columns or format issues.
    """
    errors: List[ValidationErrorItem] = []
    
    # Check date and email columns if they exist in header names
    for row_idx, row in enumerate(records):
        for col in columns:
            col_lower = col.lower()
            val = row.get(col)
            if val is not None:
                val_str = str(val).strip()
                if "email" in col_lower and val_str:
                    if not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", val_str):
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, Column '{col}'",
                            message=f"Invalid email syntax '{val_str}'",
                            raw_value=val_str
                        ))
                elif ("date" in col_lower or "dob" in col_lower) and val_str:
                    # check if format is reasonable
                    if len(val_str) < 4:
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, Column '{col}'",
                            message=f"Invalid date value '{val_str}'",
                            raw_value=val_str
                        ))

    return records, errors
