from typing import Optional
import typer
from utils import get_client

app = typer.Typer()


#---- 1.c.i ----
@app.command("create-table")
def create_table(
    table_name: str = typer.Argument(..., help="DynamoDB table name"),
    partition_key: str = typer.Option(..., "--pk", help="Partition key name (e.g. 'id')"),
    pk_type: str = typer.Option("S", "--pk-type", help="Partition key type: S, N, or B"),
):
    """Create a new DynamoDB table."""

    client = get_client("dynamodb")

    client.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": partition_key, "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": partition_key, "AttributeType": pk_type}],
        BillingMode="PAY_PER_REQUEST",
    )

#---- 1.c.ii ----
@app.command("populate")
def populate_from_s3(
    table_name: str = typer.Argument(..., help="Target DynamoDB table"),
    bucket_name: str = typer.Argument(..., help="S3 bucket containing the data file"),
    s3_key: str = typer.Argument(..., help="S3 object key (e.g. 'data.csv' or 'data.json')"),
):
    """Download a file from S3 and batch-write its rows into DynamoDB."""
    print(f"Populating '{table_name}' from s3://{bucket_name}/{s3_key}...")

    s3 = get_client("s3")
    dynamo = get_resource("dynamodb")
    table = dynamodb.Table(table_name)

     # grab the file from s3 and parse each line as a DynamoDB JSON item
    response = s3.get_object(Bucket=bucket_name, Key=s3_key)
    lines = response["Body"].read().decode("utf-8").splitlines()

    # need to convert DynamoDB JSON format ({"S": "value"}) to normal python dicts
    deserializer = TypeDeserializer()

    with table.batch_writer() as batch:
        for line in lines:
            if not line.strip():
                continue
            dynamo_item = json.loads(line)['Item']
            native_item = {
                k: deserializer.deserialize(v) for k, v in dynamo_item.items()
            }
            batch.put_item(Item=native_item)
            
#---- 1.c.iii ----
@app.command("get")
def get_data(
    table_name: str = typer.Argument(..., help="DynamoDB table name"),
    pk_value: Optional[str] = typer.Option(None, "--pk-value", help="Partition key value for single item"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max items when scanning"),
):
    """Get items from a DynamoDB table (single item by PK, or scan)."""
    client = get_client("dynamodb")

    if pk_value:
        print(f"Getting item with pk={pk_value} from '{table_name}'...")
        # TODO: client.get_item(...)
    else:
        print(f"Scanning '{table_name}' (limit {limit})...")
        # TODO: client.scan(...)


#---- 1.c.iv ----
@app.command("delete-table")
def delete_table(
    table_name: str = typer.Argument(..., help="Table to delete"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a DynamoDB table."""
    if not confirm:
        typer.confirm(f"Are you sure you want to delete table '{table_name}'?", abort=True)

    client = get_client("dynamodb")
    client.delete_table(TableName=table_name)
