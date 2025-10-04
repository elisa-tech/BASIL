from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String


class Base(DeclarativeBase):
    dt_format_str = "%Y-%m-%d %H:%M"
    dt_short_format_str = "%d %b %y %H:%M"

    STATUS_NEW = 'NEW'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_REWORK = 'REWORK'

    @classmethod
    def get_field_constraints(cls):
        """
        Returns a dictionary with database field information including max lengths for string fields.

        Returns:
            dict: Dictionary with field names as keys and field information as values.
                 For string fields, includes 'max_length' if defined.
                 For all fields, includes 'type', 'nullable', and 'primary_key' information.
        """
        from sqlalchemy import inspect

        # Get the table metadata
        mapper = inspect(cls)
        constraints = {}

        for column in mapper.columns:
            field_info = {
                'type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key
            }

            # Check if it's a String type with length constraint
            if hasattr(column.type, 'length') and column.type.length is not None:
                field_info['max_length'] = column.type.length
            elif isinstance(column.type, String) and hasattr(column.type, 'length') and column.type.length is not None:
                field_info['max_length'] = column.type.length

            constraints[column.name] = field_info

        return constraints
