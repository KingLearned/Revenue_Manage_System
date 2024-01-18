import gc


class ModelDecorators:
    @staticmethod
    def wrap_is_existing_and_former_instance(func):
        def func_to_execute(self, *args, **kwargs):
            kwargs["is_existing"] = self.is_instance_exist()
            kwargs["former_instance"] = kwargs["is_existing"] and self.current_instance
            return func(self, *args, **kwargs)

        func_to_execute.__name__ = func.__name__
        return func_to_execute

    @staticmethod
    def detect_change_in_field_on_save(fields: tuple, callback_on_change):
        def func(func_):
            def func_to_execute(self, *args, **kwargs):
                if fields and kwargs.get("is_existing"):
                    previous_instance = kwargs.get("former_instance")
                    prev_data = tuple(
                        getattr(previous_instance, field) for field in fields
                    )
                    func_(self, *args, **kwargs)
                    new_data = tuple(getattr(self, field) for field in fields)
                    if new_data != prev_data:
                        del new_data
                        del prev_data
                        gc.collect()
                        callback_on_change(self)
                    else:
                        del new_data
                        del prev_data
                        gc.collect()
                else:
                    return func_(self, *args, **kwargs)

            func_to_execute.__name__ = func_.__name__
            return func_to_execute

        return func
