tmp_count = 0
label_count = 0

def make_temporary() -> str:
    global tmp_count
    tmp = f'tmp.{tmp_count}'
    tmp_count += 1
    return tmp


def make_label() -> str:
    global label_count
    label_count += 1
    return f'label_{label_count}'