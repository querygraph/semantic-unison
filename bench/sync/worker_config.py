"""Pure benchmark worker selection and conservative endpoint CPU declarations."""
WORKER_CHOICES = (1, 2, 3, 4, 6, 8, 18, 36)


def parse_workers(text):
    try:
        values = ['auto' if word == 'auto' else int(word) for word in text.split(',')]
    except (ValueError, AttributeError):
        raise ValueError('workers must be comma-separated integers or auto') from None
    if (not values or len(set(values)) != len(values)
            or any(value != 'auto' and value not in WORKER_CHOICES for value in values)):
        raise ValueError('workers must be unique values from 1,2,3,4,6,8,18,36,auto')
    return values


def endpoint_bound(selection, ceiling=None):
    if ceiling is not None and (type(ceiling) is not int or not 1 <= ceiling <= 36):
        raise ValueError('endpoint CPU budget must be 1..36')
    if selection == 'auto':
        if ceiling is None:
            raise ValueError('auto workers require an explicit endpoint CPU budget')
        return ceiling
    if type(selection) is not int or selection not in WORKER_CHOICES:
        raise ValueError('invalid worker selection')
    if ceiling is not None and selection > ceiling:
        raise ValueError('explicit worker selection exceeds endpoint CPU budget')
    return selection


def worker_options(selection, ceiling=None):
    bound = endpoint_bound(selection, ceiling)
    flags = ['-semanticworkers', '0' if selection == 'auto' else str(selection)]
    if ceiling is not None:
        flags += ['-semanticcpubudget', str(ceiling)]
    return flags + ['-maxthreads', str(max(2, bound))]
