"""
Created on 17 Mar 2024

@author: si
"""
import boto3

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
    @return list of dict. with keys-

    """
    raise NotImplementedError("TODO - I am here")
