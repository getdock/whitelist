def chunks(iterable, chunk_size):
    """
    breaks iterable on evenly sized chunks
    """
    it = iter(iterable)
    while True:
        chunk = []
        for i in range(chunk_size):
            try:
                chunk.append(next(it))
            except StopIteration:
                break
        if chunk:
            yield chunk
        else:
            break
