from functools import wraps

import distributor  # pylint: disable=import-error


# method calling injection
def inject(target_function, new_function):
    @wraps(target_function)
    def _inject(*args, **kwargs):
        return new_function(target_function, *args, **kwargs)

    return _inject


# method injection
def inject_method_to(target_object, target_function_name):
    def _inject_to(new_function):
        target_function = getattr(target_object, target_function_name)

        setattr(target_object, target_function_name,
                inject(target_function, new_function))

        return new_function

    return _inject_to


# class field injection
def inject_field_to(target_object, target_function, operator):
    def _inject_to(new_getter):
        target_field = getattr(target_object, target_function)
        target_getter = target_field.getter

        injected_getter = inject(target_getter, new_getter)
        new_field = distributor.fields.Field(getter=injected_getter, op=operator)

        setattr(target_object, target_function, new_field)

        return new_getter

    return _inject_to


# class property injection
def inject_property_to(target_object, target_function):
    def _inject_to(new_getter):
        target_property = getattr(target_object, target_function)
        target_getter = target_property.__get__

        injected_getter = inject(target_getter, new_getter)
        new_property = property(injected_getter)

        setattr(target_object, target_function, new_property)

        return new_getter

    return _inject_to
