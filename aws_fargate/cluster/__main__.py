"""
Build an ECS cluster with a Farget task definition for fossa.

See top level README.md
"""
import os

import pulumi
from pulumi_aws import ec2, ecr, ecs, iam


pulumi_organisation = os.environ["PULUMI_ORGANISATION"]

config = pulumi.Config()
aws_config = pulumi.Config("aws")
aws_region = aws_config.require("region")

stack_name = pulumi.get_stack()
stack_label = f"cluster_{stack_name}"
network_outputs = pulumi.StackReference(f"{pulumi_organisation}/network/{stack_name}")
vpc_id = network_outputs.require_output("vpc_id")
subnets = network_outputs.require_output("subnets")
private_subnet_id = subnets[f"networks_{stack_name}_subnet_b"]["id"]

# ECS cluster
app_cluster = ecs.Cluster("fossa-cluster")


# IAM role for Fargate
app_exec_role = iam.Role(
    "app-exec-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }""",
)

# Attaching execution permissions to the exec role
exec_policy_attachment = iam.RolePolicyAttachment(
    "app-exec-policy",
    role=app_exec_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# IAM role used by Fargate to manage tasks
app_task_role = iam.Role(
    "app-task-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }""",
)

# Attaching execution permissions to the task role
task_policy_attachment = iam.RolePolicyAttachment(
    "app-access-policy",
    role=app_task_role.name,
    policy_arn=iam.ManagedPolicy.AMAZON_ECS_FULL_ACCESS,
)


# TODO - will become a fossa image
flask_image = ecr.get_image(image_tag="flask_xy", repository_name="demo")


# Creating a task definition for the Flask instance.
fossa_task_definition = ecs.TaskDefinition(
    "fossa-task-definition",
    family="fossa-task-family",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=app_exec_role.arn,
    task_role_arn=app_task_role.arn,
    container_definitions=pulumi.Output.json_dumps(
        [
            {
                "name": "fossa-container",
                "image": flask_image.image_uri,
                "memory": 512,
                "essential": True,
                "portMappings": [{"containerPort": 5000, "hostPort": 5000, "protocol": "tcp"}],
                "environment": [
                    {"name": "HELLO", "value": "WORLD"},
                ],
            }
        ]
    ),
)

port = 5000
label = f"secgrp_{stack_name}_{port}"
fossa_security_groups = [
    ec2.SecurityGroup(
        label,
        description="cluster ingress",
        ingress=[
            {
                "protocol": "tcp",
                "from_port": port,
                "to_port": port,
                "cidr_blocks": ["0.0.0.0/0"],
            },
        ],
        egress=[
            {
                "protocol": "-1",
                "from_port": 0,
                "to_port": 0,
                "cidr_blocks": ["0.0.0.0/0"],
            },
        ],
        vpc_id=vpc_id,
    ),
]


fossa_service = ecs.Service(
    "fossa-service",
    cluster=app_cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=fossa_task_definition.arn,
    wait_for_steady_state=False,
    network_configuration=ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=[private_subnet_id],
        security_groups=fossa_security_groups,
    ),
)
