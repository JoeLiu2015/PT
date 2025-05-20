import sys
import time
import ptctx

def print_logo():
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

if __name__ == '__main__':
  no_logo, no_cost_time = False, False
  if '-nologo' in sys.argv:
    no_logo = True
    sys.argv.remove('-nologo')
  if '-nocosttime' in sys.argv:
    no_cost_time = True
    sys.argv.remove('-nocosttime')

  # print logo
  if not no_logo:
    print_logo()

  # execute
  start_time = time.time()
  ptctx.PT.execute(sys.argv)

  # print cost time
  if not no_cost_time:
    execution_time = time.time() - start_time
    print(f"(Cost time: {execution_time} seconds)")


