KB = 1_000
MB = 1_000_000
GB = 1_000_000_000

def format_bytes(bytes: int):
  if bytes is None:
    return None

  if bytes < KB:
    return f'{bytes} B'
  elif bytes < MB:
    return f'{bytes / KB:.1f} KB'
  elif bytes < GB:
    return f'{bytes / MB:.1f} MB'
  else:
    return f'{bytes / GB:.1f} GB'
