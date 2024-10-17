import sys
import time
import ptctx

if __name__ == '__main__':
  print('Python version: ', sys.version)
  start_time = time.time()
  ptctx.PT.execute(sys.argv)
  execution_time = time.time() - start_time
  print(f"Cost time: {execution_time} seconds")
