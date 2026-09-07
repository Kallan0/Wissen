"""
Chunked downloader: reconnects every CHUNK_SIZE bytes using HTTP Range requests.
This works around SSL inspection proxies that corrupt large TLS streams.
"""
import ssl, urllib.request, os, sys, time

URL = "https://files.pythonhosted.org/packages/eb/ce/0f7be6e5d0feafa2cda54b12e6542afeea7dea89d2d411e14da90f8abb96/chromadb-1.5.9-cp39-abi3-win_amd64.whl"
OUTFILE = "chromadb-1.5.9-cp39-abi3-win_amd64.whl"
CHUNK_SIZE = 512 * 1024  # 512 KB per reconnect
MAX_RETRIES = 10

def make_ctx():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def get_total_size():
    req = urllib.request.Request(URL, method="HEAD")
    with urllib.request.urlopen(req, context=make_ctx()) as r:
        return int(r.headers.get("Content-Length", 0))

def download_range(start, end):
    req = urllib.request.Request(URL)
    req.add_header("Range", f"bytes={start}-{end-1}")
    with urllib.request.urlopen(req, context=make_ctx(), timeout=30) as r:
        return r.read()

def main():
    downloaded = os.path.getsize(OUTFILE) if os.path.exists(OUTFILE) else 0
    total = get_total_size()
    if total == 0:
        print("ERROR: Could not get file size", flush=True)
        sys.exit(1)

    print(f"Total size: {total/1024/1024:.1f} MB, already have: {downloaded/1024/1024:.1f} MB", flush=True)

    if downloaded >= total:
        print("Already fully downloaded!", flush=True)
        return

    with open(OUTFILE, "ab") as f:
        pos = downloaded
        while pos < total:
            end = min(pos + CHUNK_SIZE, total)
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = download_range(pos, end)
                    f.write(data)
                    f.flush()
                    pos += len(data)
                    pct = pos / total * 100
                    print(f"  {pct:.1f}% ({pos/1024/1024:.1f}/{total/1024/1024:.1f} MB)", flush=True)
                    break
                except Exception as e:
                    retries += 1
                    print(f"  Chunk {pos}-{end} failed (attempt {retries}): {e}", flush=True)
                    time.sleep(2)
            else:
                print(f"FATAL: Could not download chunk {pos}-{end} after {MAX_RETRIES} retries", flush=True)
                sys.exit(1)

    print(f"\nDownload complete! Saved to {OUTFILE}", flush=True)

if __name__ == "__main__":
    main()
