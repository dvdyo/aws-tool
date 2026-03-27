from typing import Optional
import typer
from utils import get_client

app = typer.Typer()


#---- 1.b.i (create) ----
@app.command("create-bucket")
def create_bucket(
    bucket_name: str = typer.Argument(..., help="Globally unique bucket name"),
    region: str = typer.Option(..., "--region", "-r", help="AWS region (e.g. eu-north-1)"),
):
    """Create a new S3 bucket."""

    client = get_client("s3", region_name=region)
    client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region},
    )

#---- 1.b.ii ----
@app.command("upload")
def upload_file(
    file_path: str = typer.Argument(..., help="Local path to the file"),
    bucket_name: str = typer.Argument(..., help="Target bucket name"),
    s3_key: Optional[str] = typer.Option(None, "--key", "-k", help="S3 object key (default: filename)"),
):
    """Upload a single file to an S3 bucket."""
    if s3_key is None:
        import os
        s3_key = os.path.basename(file_path)

    print(f"Uploading {file_path} -> s3://{bucket_name}/{s3_key}")

    client = get_client("s3")
    # TODO: client.upload_file(Filename=file_path, Bucket=bucket_name, Key=s3_key)


#---- 1.b.iii ----
@app.command("upload-folder")
def upload_folder(
    folder_path: str = typer.Argument(..., help="Local folder to upload"),
    bucket_name: str = typer.Argument(..., help="Target bucket name"),
    prefix: str = typer.Option("", "--prefix", "-p", help="S3 key prefix (virtual folder)"),
):
    """Recursively upload a local folder to an S3 bucket."""
    print(f"Uploading folder {folder_path}/ -> s3://{bucket_name}/{prefix}")

    client = get_client("s3")
    # TODO: os.walk() + client.upload_file() for each file


#---- 1.b.iv ----
@app.command("ls")
def list_objects(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    prefix: str = typer.Option("", "--prefix", "-p", help="Only list objects under this prefix"),
    show_versions: bool = typer.Option(False, "--versions", "-v", help="Show object versions"),
):
    """List files on a bucket with name, size, storage class, versions."""
    print(f"Listing s3://{bucket_name}/{prefix}  (versions={show_versions})")

    client = get_client("s3")
    # TODO: client.list_objects_v2() or client.list_object_versions()


#---- 1.b.v ----
@app.command("make-public")
def make_public(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    s3_key: str = typer.Argument(..., help="Object key to make public"),
):
    """Make a single object publicly readable."""
    print(f"Making s3://{bucket_name}/{s3_key} public...")

    client = get_client("s3")
    # TODO: client.put_object_acl(Bucket=bucket_name, Key=s3_key, ACL="public-read")


#---- 1.b.vi ----
@app.command("delete")
def delete_objects(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    prefix: str = typer.Argument(..., help="Key or prefix to delete"),
):
    """Delete a file or all files under a prefix on a bucket."""
    print(f"Deleting s3://{bucket_name}/{prefix}...")

    client = get_client("s3")
    # TODO: list + client.delete_objects(...)


#---- 1.b.vii ----
@app.command("delete-bucket")
def delete_bucket(
    bucket_name: str = typer.Argument(..., help="Bucket to delete (must be empty)"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete all objects first, then delete bucket"),
):
    """Delete an S3 bucket. Use --force to empty it first."""

    client = get_client("s3")

    while True:
        response = client.list_objects_v2(Bucket=bucket_name)
        objects = response.get("Contents", [])
        if objects:
            client.delete_objects(
                Bucket=bucket_name,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
            )
        if not response["IsTruncated"]:
            break
    client.delete_bucket(Bucket=bucket_name)

#---- bonus: list buckets ----
@app.command("list-buckets")
def list_buckets():
    """List all S3 buckets in the account."""

    client = get_client("s3")
    response = client.list_buckets()
    for bucket in response["Buckets"]:
        typer.echo(f"{bucket['Name']}")
