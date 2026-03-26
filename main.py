import typer
import ec2_commands
import s3_commands
import dynamo_commands

app = typer.Typer(help="Lab 4 AWS Automation CLI Tool")

app.add_typer(ec2_commands.app, name="ec2", help="Manage EC2 instances")
app.add_typer(s3_commands.app, name="s3", help="Manage S3 buckets")
app.add_typer(dynamo_commands.app, name="dynamodb", help="Manage DynamoDB tables")

if __name__ == "__main__":
    app()
