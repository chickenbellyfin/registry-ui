from src import util

def test_format_bytes():
  assert util.format_bytes(0) == '0 B'
  assert util.format_bytes(999) == '999 B'
  assert util.format_bytes(1_000) == '1.0 KB'
  assert util.format_bytes(999_000) == '999.0 KB'
  assert util.format_bytes(1_000_000) == '1.0 MB'
  assert util.format_bytes(999_000_000) == '999.0 MB'
  assert util.format_bytes(1_000_000_000) == '1.0 GB'
  assert util.format_bytes(1_500_000_000) == '1.5 GB'
