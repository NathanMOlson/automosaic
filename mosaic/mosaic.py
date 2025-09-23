import os
import sys

def main():
    print(f"argv: {sys.argv}")
    print(f"environ: {os.environ}")


if __name__ == "__main__":
    main()
