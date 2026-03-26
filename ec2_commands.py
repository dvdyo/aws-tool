from typing import Optional, List
import typer
from utils import get_client

app = typer.Typer()


#---- 1.a.i & ii ----
@app.command("create")
def create_instance(
    ami_id: str = typer.Argument(..., help="AMI image ID (e.g. ami-0c1ac8a41498c1a9e)"),
    instance_type: str = typer.Option("t2.micro", "--type", "-t", help="Instance type (Free Tier: t2.micro)"),
    key_name: Optional[str] = typer.Option(None, "--key", "-k", help="Name of an existing EC2 key pair for SSH"),
    security_group_ids: Optional[List[str]] = typer.Option(None, "--sg", help="Security group IDs to attach"),
    script_path: Optional[str] = typer.Option(None, "--script", "-s", help="Path to a bash script for UserData"),
):
    """Create a new EC2 instance. Optionally pass a bash bootstrap script."""

    user_data = ""
    if script_path:
        with open(script_path, "r") as f:
            user_data = f.read()

    client = get_client("ec2")
    kwargs = dict(
        ImageId=ami_id,
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
    )

    if key_name:
        kwargs["KeyName"] = key_name

    if security_group_ids:
        kwargs["SecurityGroupIds"] = security_group_ids

    if user_data:
        kwargs["UserData"] = user_data

    client.run_instances(**kwargs)
    # response = client.run_instances(**kwargs)

    # instance = response["Instances"][0]
    # typer.echo(f"Launched instance: {instance['InstanceId']}")

#---- 1.a.iii ----
@app.command("modify-sg")
def modify_security_group(
    group_id: str = typer.Argument(..., help="Security Group ID (e.g. sg-0abc123)"),
):
    """Open inbound ports 22 (SSH) and 80 (HTTP) on a security group."""

    client = get_client("ec2")

    client.authorize_security_group_ingress(
        GroupId=group_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP"}],
            },
        ],
    )


#---- 1.a.iv ----
@app.command("tag")
def tag_instance(
    instance_id: str = typer.Argument(..., help="Instance ID (e.g. i-0abc123)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New Name tag value"),
    tags: Optional[List[str]] = typer.Option(
        None, "--tag", "-t",
        help="Extra tags as Key=Value (repeatable, e.g. --tag Env=dev --tag Project=lab4)",
    ),
):
    """Set the Name tag and optionally add extra descriptive tags."""
    tag_list =[]

    if name:
        tag_list.append({"Key": "Name", "Value": name})

    if tags:
        for t in tags:
            k, v = t.split("=", 1)
            tag_list.append({"Key": k, "Value": v})
        typer.echo(f"  extra tags: {tags}")

    if not tag_list:
        typer.echo("Error: You must provide at least a --name or --tag")
        raise typer.Exit(code=1)

    client = get_client("ec2")
    client.create_tags(Resources=[instance_id], Tags=tag_list)
    
#---- 1.a.v ----
@app.command("info")
def instance_info(
    instance_id: str = typer.Argument(..., help="Instance ID"),
):
    """typer.echo detailed info: instance type, RAM, disk, IP addresses."""

    client = get_client("ec2")
    client = get_client("ec2")

    # get instance details
    reservations = client.describe_instances(InstanceIds=[instance_id])["Reservations"]
    instance = reservations[0]["Instances"][0]

    instance_type = instance["InstanceType"]
    public_ip = instance.get("PublicIpAddress", "N/A")
    private_ip = instance.get("PrivateIpAddress", "N/A")
    state = instance["State"]["Name"]
    security_groups = [sg["GroupId"] for sg in instance["SecurityGroups"]]

    # get RAM and CPU for that instance type
    type_info = client.describe_instance_types(InstanceTypes=[instance_type])["InstanceTypes"][0]
    ram_mb = type_info["MemoryInfo"]["SizeInMiB"]
    vcpus = type_info["VCpuInfo"]["DefaultVCpus"]
    storage = type_info.get("InstanceStorageInfo", {}).get("TotalSizeInGB", "EBS only")

    typer.echo(f"Instance ID:      {instance_id}")
    typer.echo(f"State:            {state}")
    typer.echo(f"Type:             {instance_type}")
    typer.echo(f"vCPUs:            {vcpus}")
    typer.echo(f"RAM:              {ram_mb} MiB ({ram_mb // 1024} GiB)")
    typer.echo(f"Storage:          {storage}")
    typer.echo(f"Public IP:        {public_ip}")
    typer.echo(f"Private IP:       {private_ip}")
    typer.echo(f"Security Groups:  {security_groups}")

#---- 1.a.vi ----
@app.command("state")
def manage_state(
    instance_id: str = typer.Argument(..., help="Instance ID"),
    action: str = typer.Argument(..., help="Action: stop | start | terminate"),
):
    """Stop, start, or terminate an EC2 instance."""
    if action not in ("stop", "start", "terminate"):
        typer.echo(f"Unknown action '{action}'. Use: stop, start, or terminate.")
        raise typer.Exit(code=1)

    client = get_client("ec2")
    if action == "start":
         client.start_instances(InstanceIds=[instance_id])
    elif action == "stop":
        client.stop_instances(InstanceIds=[instance_id])
    elif action == "terminate":
        client.terminate_instances(InstanceIds=[instance_id])


#---- bonus: key pair ----
@app.command("create-key")
def create_key_pair(
    key_name: str = typer.Argument(..., help="Name for the new key pair"),
    output_path: str = typer.Option("./key.pem", "--out", "-o", help="Where to save the .pem file"),
):
    """Create an EC2 key pair and save the private key locally."""

    client = get_client("ec2")

    response = client.create_key_pair(KeyName=key_name)
    private_key = response["KeyMaterial"]

    with open(output_path, "w") as f:
        f.write(private_key)

    import os
    os.chmod(output_path, 0o400)

