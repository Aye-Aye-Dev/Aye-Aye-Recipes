"""
Build an ECS cluster with a Farget task definition for fossa.

See top level README.md
"""
import os
import time

import boto3
import pulumi
from pulumi_aws import cloudwatch, ec2, ecr, ecs, iam, servicediscovery


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
fossa_port = 2345
rabbitmq_port = 5672
# TODO - build the ECR
ecr_repository_name = "demo"


def simple_security_groups(*ports):
    security_groups = []
    for port in ports:
        label = f"secgrp_{stack_name}_{port}"
        sg = ec2.SecurityGroup(
            label,
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
        )
        security_groups.append(sg)
    return security_groups


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

log_group_name = "ecs_logs"
log_group = cloudwatch.LogGroup(
    log_group_name,
    name=log_group_name,
    retention_in_days=7,
)

# fossa_namespace = servicediscovery.PrivateDnsNamespace(
#     "fossa",
#     name="fossa",
#     description="Fossa workers namespace",
#     vpc=vpc_id,
# )
#
# fossa_service_discover = servicediscovery.Service(
#     "fossa_service_discover",
#     name="fossa_service_discover",
#     dns_config=servicediscovery.ServiceDnsConfigArgs(
#         namespace_id=fossa_namespace.id,
#         dns_records=[
#             servicediscovery.ServiceDnsConfigDnsRecordArgs(
#                 ttl=10,
#                 type="A",
#             )
#         ],
#     ),
#     health_check_config=servicediscovery.ServiceHealthCheckConfigArgs(
#         failure_threshold=10,
#         resource_path="path",
#         type="HTTP",
#     ),
# )

http_namespace = servicediscovery.HttpNamespace(
    "fossa_http_namespace",
    name="fossa_workloads",
    description="HTTP Namespace for Fossa",
)


rabbitmq_task_definition = ecs.TaskDefinition(
    "rabbitmq-task-definition",
    family="rabbitmq-task-family",
    cpu="256",
    memory="2048",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=app_exec_role.arn,
    task_role_arn=app_task_role.arn,
    container_definitions=pulumi.Output.json_dumps(
        [
            {
                "name": "fossa-container",
                "image": "rabbitmq:3",
                "memory": 2048,
                "essential": True,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.name,
                        "awslogs-region": aws_region,
                        "awslogs-stream-prefix": "rabbit_mq",
                    },
                },
            }
        ]
    ),
)

rabbitmq_service = ecs.Service(
    "rabbitmq-service",
    cluster=app_cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=rabbitmq_task_definition.arn,
    wait_for_steady_state=False,
    network_configuration=ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=[private_subnet_id],
        security_groups=simple_security_groups(rabbitmq_port),
    ),
    # service_registries=[ecs.ServiceServiceRegistriesArgs(registry_arn=http_namespace.arn)],
)


def build_rabbitmq_url(*callback_args):
    """
    Get the IP address of the rabbit mq task/container. This is a hack!
    Incorrect methodology warning - the ECS cluster should declare the RabbitMQ service using
    Cloud Map or some other service discovery mechanism.

    @returns (str) ip address after checking it's a single task in this service
    """
    cluster_arn = callback_args[0][0]
    service_arn = callback_args[0][1]
    ecs = boto3.client("ecs", region_name=aws_region)

    # just fing tasks for the service_arn which is the RabbitMq service
    tasks = {"taskArns": []}
    while len(tasks["taskArns"]) == 0:
        time.sleep(3)
        tasks = ecs.list_tasks(cluster=cluster_arn, serviceName=service_arn)

    while True:
        task_details = ecs.describe_tasks(cluster=cluster_arn, tasks=tasks["taskArns"])
        # this won't work if a container failed and was replaced but is quicker to return is a
        # container isn't yet 'RUNNING'
        assert len(task_details["tasks"]) == 1, "RabbitMq is expected to have one task"
        assert len(task_details["tasks"][0]["containers"]) == 1, "Expecting one container"

        c = task_details["tasks"][0]["containers"][0]
        if (
            "networkInterfaces" in c
            and len(c["networkInterfaces"]) > 0
            and "privateIpv4Address" in c["networkInterfaces"][0]
        ):
            container_ip = c["networkInterfaces"][0]["privateIpv4Address"]
            break
        else:
            time.sleep(3)

    return f"amqp://guest:guest@{container_ip}"


rabbitmq_url = pulumi.Output.all(app_cluster.arn, rabbitmq_service.id).apply(build_rabbitmq_url)

# Creating a task definition for the Fossa worker nodes
flask_image = ecr.get_image(image_tag="fossa-worker", repository_name=ecr_repository_name)
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
                "portMappings": [
                    {"containerPort": fossa_port, "hostPort": fossa_port, "protocol": "tcp"}
                ],
                "environment": [
                    {"name": "RABBITMQ_URL", "value": rabbitmq_url},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.name,
                        "awslogs-region": aws_region,
                        "awslogs-stream-prefix": "fossa_worker",
                    },
                },
            }
        ]
    ),
)


fossa_security_groups = simple_security_groups(fossa_port)

fossa_service = ecs.Service(
    "fossa-service",
    cluster=app_cluster.arn,
    desired_count=2,
    launch_type="FARGATE",
    task_definition=fossa_task_definition.arn,
    wait_for_steady_state=False,
    network_configuration=ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=[private_subnet_id],
        security_groups=fossa_security_groups,
    ),
)
