import argparse
import hashlib
import os
import sqlite3
import tarfile
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import boto3


def main():
    parser = argparse.ArgumentParser(description="Download and verify a Learning OS backup without replacing production data.")
    parser.add_argument("--key", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    client = boto3.client("s3", endpoint_url=os.getenv("BACKUP_S3_ENDPOINT") or None)
    bucket = os.environ["BACKUP_S3_BUCKET"]
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="learning-os-restore-") as temp:
        archive = Path(temp) / "backup.tar.gz"
        client.download_file(bucket, args.key, str(archive))
        expected = client.head_object(Bucket=bucket, Key=args.key).get("Metadata", {}).get("sha256")
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if not expected or expected != actual: raise RuntimeError("Backup checksum mismatch.")
        with tarfile.open(archive, "r:gz") as tar: tar.extractall(output, filter="data")
    database = output / "database" / "learning_os.db"
    connection = sqlite3.connect(database)
    result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    connection.close()
    if result != "ok": raise RuntimeError(f"SQLite integrity check failed: {result}")
    print(f"Verified restore at {output}. Production data was not replaced.")


if __name__ == "__main__": main()
