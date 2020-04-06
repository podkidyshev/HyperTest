def prettify_validation_error(err_detail):
    if isinstance(err_detail, list):
        return err_detail[0]
    elif isinstance(err_detail, str):
        return err_detail

    errors = {}

    for field, value in err_detail.items():
        if isinstance(value, str):
            errors[field] = value
            continue

        if isinstance(value, list) and len(value):
            errors[field] = value[0]

    return errors
