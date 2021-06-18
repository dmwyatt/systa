from systa.experimental.decorators.listen_to import func_ranges


def run():
    for function in func_ranges:
        print(f"running {function.__name__} on ranges: {func_ranges[function]}")
