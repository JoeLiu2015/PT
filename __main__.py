import sys
import ptctx

if __name__ == '__main__':
  print('Python version: ', sys.version)
  ptctx.PT.execute(sys.argv)
