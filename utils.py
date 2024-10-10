tmp_count = 0

def make_temporary() -> str:
    global tmp_count
    tmp = f'tmp.{tmp_count}'
    tmp_count += 1
    return tmp