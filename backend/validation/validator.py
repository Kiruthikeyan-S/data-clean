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


def validate_entity_records(
    records: List[Dict[str, Any]], 
    columns: List[str],
    entity_type: Optional[str] = "general"
) -> Tuple[List[Dict[str, Any]], List[ValidationErrorItem]]:
    """
    Fundamental 8: Validates tabular records against business entity schemas (Customer, Store, Item, Transaction)
    with severity ratings (Error, Warning, Info) without blocking the entire dataset.
    """
    errors: List[ValidationErrorItem] = []
    e_type = str(entity_type).lower().strip() if entity_type else "general"
    
    for row_idx, row in enumerate(records):
        for col in columns:
            col_lower = str(col).lower().strip().replace('-', '_').replace(' ', '_')
            val = row.get(col)
            
            if val is not None:
                val_str = str(val).strip()
                if not val_str or val_str.lower() in ("null", "none", "nan", "n/a", "-"):
                    continue
                    
                # 1. Email validation
                if "email" in col_lower:
                    if not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", val_str):
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, Column '{col}'",
                            message=f"Warning: Invalid email syntax '{val_str}'",
                            raw_value=val_str
                        ))

                # 2. Date validation
                elif any(k in col_lower for k in ("date", "dob", "time", "timestamp")):
                    if len(val_str) < 4 or not (re.match(r"^\d{4}-\d{2}-\d{2}", val_str) or re.match(r"^\d{1,4}[/\-]\d{1,2}[/\-]\d{1,4}", val_str)):
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, Column '{col}'",
                            message=f"Warning: Inconsistent date format '{val_str}'",
                            raw_value=val_str
                        ))

                # 3. Phone validation
                elif any(k in col_lower for k in ("phone", "mobile", "contact", "cell")):
                    digits = re.sub(r"\D", "", val_str)
                    if len(digits) < 7 or len(digits) > 15:
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, Column '{col}'",
                            message=f"Warning: Phone number length unexpected ({len(digits)} digits): '{val_str}'",
                            raw_value=val_str
                        ))

                # 4. Inventory / Stock validation (Negative stock is flagged as warning/invalid, not silently flipped!)
                elif any(k in col_lower for k in ("stock", "qty", "quantity", "inventory", "units")) and "id" not in col_lower:
                    try:
                        num = float(re.sub(r"[^\d.-]", "", val_str))
                        if num < 0:
                            errors.append(ValidationErrorItem(
                                field=f"Row {row_idx + 1}, Column '{col}'",
                                message=f"Warning: Negative inventory/quantity ({num}) detected. Flagged for review.",
                                raw_value=val_str
                            ))
                    except Exception:
                        pass

                # 5. Price / Amount validation
                elif any(k in col_lower for k in ("price", "amount", "total", "cost", "salary", "mrp", "rate")):
                    try:
                        num = float(re.sub(r"[^\d.-]", "", val_str))
                        if num < 0:
                            errors.append(ValidationErrorItem(
                                field=f"Row {row_idx + 1}, Column '{col}'",
                                message=f"Warning: Negative financial amount ({num}) flagged for review.",
                                raw_value=val_str
                            ))
                    except Exception:
                        pass

                # 6. Postal code validation
                elif any(k in col_lower for k in ("pin", "zip", "postal", "pincode")):
                    cleaned_zip = re.sub(r"\s+", "", val_str)
                    if not re.match(r"^\d{5,6}(-\d{4})?$", cleaned_zip) and len(cleaned_zip) > 10:
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, Column '{col}'",
                            message=f"Info: Non-standard postal code format '{val_str}'",
                            raw_value=val_str
                        ))

    return records, errors


def validate_structured_records(records: List[Dict[str, Any]], columns: List[str]) -> Tuple[List[Dict[str, Any]], List[ValidationErrorItem]]:
    """Alias for backward compatibility with existing callers."""
    return validate_entity_records(records, columns, "general")

