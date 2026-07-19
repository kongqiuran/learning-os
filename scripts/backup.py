import hashlib
import os
import sqlite3
import tarfile
import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import boto3
from boto3.s3.transfer import TransferConfig

from src.config import DATA_DIR, UPLOAD_DIR
from src.database.connection import DATABASE_URL
from src.ops import send_alert

GIB = 1024 * 1024 * 1024


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    bucket = os.environ["BACKUP_S3_BUCKET"]
    prefix = os.getenv("BACKUP_S3_PREFIX", "learning-os").strip("/")
    endpoint = os.getenv("BACKUP_S3_ENDPOINT") or None
    database_path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    with tempfile.TemporaryDirectory(prefix="learning-os-backup-") as temp:
        root = Path(temp)
        snapshot = root / "learning_os.db"
        source = sqlite3.connect(database_path)
        target = sqlite3.connect(snapshot)
        source.backup(target)
        target.close(); source.close()
        archive = root / f"learning-os-{stamp}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(snapshot, arcname="database/learning_os.db")
            if UPLOAD_DIR.exists(): tar.add(UPLOAD_DIR, arcname="uploads")
        checksum = sha256(archive)
        key = f"{prefix}/daily/{archive.name}"

        client = boto3.client("s3", endpoint_url=endpoint)
        config = TransferConfig(
            multipart_threshold=GIB,
            multipart_chunksize=GIB,
        )

        client.upload_file(
            str(archive),
            bucket,
            key,
            ExtraArgs={
                "Metadata": {"sha256": checksum},
                "ServerSideEncryption": "AES256",
            },
            Config=config,
        )
        head = client.head_object(Bucket=bucket, Key=key)
        if head.get("Metadata", {}).get("sha256") != checksum:
            raise RuntimeError("Backup checksum metadata verification failed.")
        if now.day == 1:
            client.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": key}, Key=f"{prefix}/monthly/{archive.name}", ServerSideEncryption="AES256", MetadataDirective="COPY")
        prune(client, bucket, f"{prefix}/daily/", 30)
        prune(client, bucket, f"{prefix}/monthly/", 12)
        print(f"Backup uploaded: s3://{bucket}/{key} sha256={checksum}")


def prune(client, bucket, prefix, keep):
    objects = sorted(client.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", []), key=lambda item: item["LastModified"], reverse=True)
    for item in objects[keep:]: client.delete_object(Bucket=bucket, Key=item["Key"])


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        send_alert("backup_failed", "Production backup failed", error=type(exc).__name__)
        raise
