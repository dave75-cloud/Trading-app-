import argparse
from ingest.polygon_loader import download_range
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='date_from', required=True)
    ap.add_argument('--to', dest='date_to', required=True)
    ap.add_argument('--out', dest='out_dir', required=True)
    ap.add_argument('--symbol', default='GBPUSD')
    ap.add_argument('--api_key', required=True)
    args = ap.parse_args()
    rows = download_range(args.api_key, args.date_from, args.date_to, args.out_dir, symbol=args.symbol)
    print(f"Wrote {rows} rows to {args.out_dir}")
if __name__ == '__main__':
    main()
