"""
A new VPC with two subnets. Not much redundancy but simple to work with.

Subnet a is expected to have a route out to the public internet. See the 'gateway' sub-project.

See top level README.md
"""
import pulumi
from pulumi_aws import ec2


config = pulumi.Config()
aws_config = pulumi.Config("aws")

aws_region = aws_config.require("region")

stack_name = pulumi.get_stack()
stack_label = f"networks_{stack_name}"

cidr_block_template = "192.168.{subnet}.0{netmask}"

base_vpc = ec2.Vpc(
    stack_label,
    cidr_block=cidr_block_template.format(subnet="0", netmask="/16"),
    tags={
        "Name": stack_label,
    },
)
pulumi.export("vpc_id", base_vpc.id)

gateway = ec2.InternetGateway(
    f"{stack_label}_gateway",
    vpc_id=base_vpc.id,
    tags={
        "Name": stack_label,
    },
)

# 'a' is the public subnet, 'b' the private one for the cluster. The lettered label must be a valid
# availability zone name in the AWS region
subnet_az_labels = ["a", "b"]

route_label = f"{stack_label}_public_route"
route_table_public = ec2.RouteTable(
    route_label,
    vpc_id=base_vpc.id,
    routes=[
        ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=gateway.id,
        ),
    ],
    tags={
        "Name": route_label,
    },
)

subnets = {}
for subnet_idx, subnet_az in enumerate(subnet_az_labels):
    subnet_label = f"{stack_label}_subnet_{subnet_az}"
    subnet = subnet_idx + 1  # the 1 is arbitrary spacing

    subnet = ec2.Subnet(
        subnet_label,
        vpc_id=base_vpc.id,
        cidr_block=cidr_block_template.format(subnet=subnet, netmask="/24"),
        availability_zone=aws_region + subnet_az,
        tags={
            "Name": subnet_label,
        },
    )

    # 'a' is the public subnet
    # route for 'b' is created in the gateway sub-project.
    if subnet_az == "a":
        route_table_association = ec2.RouteTableAssociation(
            f"{stack_label}_route_assoc_{subnet_label}",
            subnet_id=subnet.id,
            route_table_id=route_table_public.id,
        )
    subnets[subnet_label] = subnet

# It's quite a bulky doc that fills a lot of the console if all details of all subnets are exported
# so stick with the details that are needed elsewhere.
subnets_extract = {}
for subnet_az_labels, subnet_params in subnets.items():
    subnets_extract[subnet_az_labels] = {
        "cidr_block": subnet_params.cidr_block,
        "id": subnet_params.id,
    }
pulumi.export("subnets", subnets_extract)
