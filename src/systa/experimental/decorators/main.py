from systa.experimental.decorators import filter_by, func_ranges, func_stack, listen_to


@filter_by.is_text("lolhmm")
# @filter_by.has_hmm
# @filter_by.has_lol
@listen_to.maximize
@listen_to.restore
def my_func(data):
    print("in my func")


f, w = list(func_stack.items())[0]
assert w == my_func

print("==================")
w("lol hmm")
print("==================")
print(func_ranges)
print(func_stack)
