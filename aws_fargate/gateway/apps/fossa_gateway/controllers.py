"""
Created on 17 Mar 2024

@author: si
"""
import boto3
import requests

# TODO - get AWS region from config
ecs = boto3.client("ecs", region_name="eu-west-2")


def cluster_arns():
    """
    @return: list of str - the ARNs of available clusters
    """
    r = ecs.list_clusters()
    return r["clusterArns"]


def task_summary(cluster_arn):
    """
    Some details about running tasks in a cluster.

    @param cluster_arn: (str)
    @return list of dict. All taken from AWS/boto3 api. If key not present, None is returned.
        with keys-
        - startedAt
        - lastStatus
        - group
        - ipv4_private
        - task_id
    """
    if cluster_arn not in cluster_arns():
        raise ValueError("Unknown cluster arn")

    tasks = ecs.list_tasks(cluster=cluster_arn)

    if "taskArns" not in tasks or len(tasks["taskArns"]) == 0:
        return []

    describe_tasks = ecs.describe_tasks(
        cluster=cluster_arn,
        tasks=tasks["taskArns"],
    )

    copy_fields = ["startedAt", "lastStatus", "group"]
    ts = []
    for task_details in describe_tasks["tasks"]:
        summary = {f: task_details.get(f) for f in copy_fields}

        summary["ipv4_private"] = None
        if len(task_details["containers"]) > 0:
            network_interfaces = task_details["containers"][0].get("networkInterfaces", [])
            if len(network_interfaces) > 0:
                summary["ipv4_private"] = network_interfaces[0].get("privateIpv4Address")

        if "taskArn" in task_details:
            arn_parts = task_details["taskArn"].split("/")
            if len(arn_parts) > 0:
                summary["task_id"] = arn_parts[-1]

        ts.append(summary)

    return ts


def fossa_node_info(fossa_node_port, cluster_arn, fossa_node_ipv4):
    """
    Query a Fossa worker node.

    This function is only needed in an environment where the nodes aren't reachable from the client
    using the gateway. e.g. private fossa nodes with a publically accessable gateway.

    @param cluster_arn: (str)
    @param fossa_node_ipv4: (str)
    @return: dict - see Fossa project :func:`fossa.views.api.node_info`
    """

    valid_ipv4 = [ts["ipv4_private"] for ts in task_summary(cluster_arn)]
    if fossa_node_ipv4 not in valid_ipv4:
        known_nodes = ",".join(valid_ipv4)
        raise ValueError(f"Unknown task: {fossa_node_ipv4} isn't in {known_nodes}")

    fossa_node_info_url = f"http://{fossa_node_ipv4}:{fossa_node_port}/api/0.01/node_info"
    r = requests.get(fossa_node_info_url)

    if r.status_code != 200:
        msg = (
            f"The Fossa node request returned http_status={r.status_code} for "
            f"url={fossa_node_info_url}"
        )
        raise ValueError(msg)

    return r.json()
