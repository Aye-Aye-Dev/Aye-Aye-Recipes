"""
Place a tiny EC2 instance on the public subnet created by the 'network' subproject. Make the
instance into a NAT gateway that also hosts a tiny web app for accessing nodes in the cluster.

See top level README.md
"""
import os

import pulumi
from pulumi_aws import ec2


pulumi_organisation = os.environ["PULUMI_ORGANISATION"]

config = pulumi.Config()
ec2_keypair_name = config.require("ec2_keypair_name")

aws_config = pulumi.Config("aws")

aws_region = aws_config.require("region")

stack_name = pulumi.get_stack()
stack_label = f"gateway_{stack_name}"
network_outputs = pulumi.StackReference(f"{pulumi_organisation}/network/{stack_name}")
vpc_id = network_outputs.require_output("vpc_id")
subnets = network_outputs.require_output("subnets")
public_subnet_id = subnets[f"networks_{stack_name}_subnet_a"]["id"]
private_subnet_id = subnets[f"networks_{stack_name}_subnet_b"]["id"]

ec2_instance_size = "t4g.nano"
ec2_instance_name = "fossa_gateway"
ec2_ami_owner = "099720109477"  # Ubuntu

ami = ec2.get_ami(
    most_recent="true",
    owners=[ec2_ami_owner],
    filters=[
        ec2.GetAmiFilterArgs(name="name", values=["ubuntu/images/hvm-ssd/ubuntu-focal-20.04*"]),
        ec2.GetAmiFilterArgs(name="root-device-type", values=["ebs"]),
        ec2.GetAmiFilterArgs(name="architecture", values=["arm64"]),
    ],
)


def build_simple_security_group(port, description):
    label = f"secgrp_{stack_name}_{port}"
    pulumi_security_group = ec2.SecurityGroup(
        label,
        description=description,
        ingress=[
            {
                "protocol": "tcp",
                "from_port": port,
                "to_port": port,
                "cidr_blocks": ["0.0.0.0/0"],
            },
        ],
        egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
        vpc_id=vpc_id,
    )
    return pulumi_security_group


# The gateway is also a NAT and these security groups are on it's network interface so restrict
# which ports can be used for outgoing NAT'd connections.
security_groups = []
for port, description in [
    (22, "SSH access"),
    (80, "HTTP access"),
    (443, "HTTPS access"),
]:
    security_groups.append(build_simple_security_group(port, description))

# Create EC2 instance
ec2_instance = ec2.Instance(
    ec2_instance_name,
    instance_type=ec2_instance_size,
    vpc_security_group_ids=security_groups,
    ami=ami.id,
    key_name=ec2_keypair_name,
    associate_public_ip_address=True,
    subnet_id=public_subnet_id,
    source_dest_check=False,  # needed to act as NAT gateway
    tags={
        "Name": ec2_instance_name,
    },
)

pulumi.export("source_ami_urm", ami.arn)
pulumi.export("public_ip", ec2_instance.public_ip)
pulumi.export("instance_id", ec2_instance.id)


route_label = f"{stack_label}_private_route"
route_table_private = ec2.RouteTable(
    route_label,
    vpc_id=vpc_id,
    routes=[
        ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            network_interface_id=ec2_instance.primary_network_interface_id,
        ),
    ],
    tags={
        "Name": route_label,
    },
)

route_table_association = ec2.RouteTableAssociation(
    f"{stack_label}_route_assoc_private",
    subnet_id=private_subnet_id,
    route_table_id=route_table_private.id,
)
