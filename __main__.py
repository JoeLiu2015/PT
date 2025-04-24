import sys
import time
import ptctx

if __name__ == '__main__':
  # https://patorjk.com/software/taag/#p=display&f=Standard&t=PT%202.0
  title = r''' ____ _____   ____    ___  
|  _ \_   _| |___ \  / _ \ 
| |_) || |     __) || | | |
|  __/ | |    / __/ | |_| |
|_|    |_|   |_____(_)___/
'''
  max_len = max(len(l) for l in title.splitlines())
  sep = '=' * len(sys.version)
  offset = round((len(sep) - max_len) / 2)

  # print title
  print(sys.version)
  print(sep)
  for l in title.splitlines():
    print(' ' * offset, l)
  print(sep)

  # print cost time
  start_time = time.time()
  ptctx.PT.execute(sys.argv)
  execution_time = time.time() - start_time
  print(f"(Cost time: {execution_time} seconds)")
