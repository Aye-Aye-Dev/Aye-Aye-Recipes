# AWS Fargate

Run loads of [Fossa](https://github.com/Aye-Aye-Dev/Fossa) workers in [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) containers so the subtasks in an Aye-Aye partitioned ETL model can be run in parallel across a distributed cluster.

## Key technologies used in this recipe

* [Pulumi](https://www.pulumi.com/) as the orchestrator. Pulumi is like Terraform but easier to engage and reason with.
* [Ansible](https://www.ansible.com/) to provision the EC2 instance (because [`pulumi_command`](https://www.pulumi.com/registry/packages/command/) doesn't look quite ready)
* [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) - Containers without the complexity of Kubernetes or provisioning EC2 instances.

## Decision log

It's a highly opiniated stack so has been split into sub-modules (detailed below). Here is the background on these opiniated decisions-

* *Gateway EC2 instance* - I really really don't want public IP addresses on each task in the cluster. In part because they incur a cost but also because private IPs are slightly safer in terms of security. I want to use AWS' [ECR](https://aws.amazon.com/ecr/) (Elastic Container Registry) with [ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html) but in order to fetch images this requires a network transit to a public IP address. The obvious solution is to use a NAT gateway but a less resiliant and less expensive alternative is to use an EC2 instance for NAT. Because an EC2 instance is needed anyway as a gateway to the ECS tasks it might as well serve this purpose too. The gateway to other tasks could be done with another container plus a loadbalancer or elastic IP or probably a dozen other ways. The decision to use EC2 is because containers in ECS can't have the [source/destination check](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-networking-awsvpc.html) disabled on the ENI. 


## Running this

Run the 'Usage' section from the [top level README](../README.md).

First, [setup Pulumi](https://www.pulumi.com/docs/get-started/).

The orchestration and provisioning has been split into sub-projects. This will make it easier to pick and choose from my opiniated stack. There are 3 sub-projects which each have a corresponding sub-directory-

* networks
* gateway
* cluster


`cd` into each directory in the order they are listed above; then run the sub-module with these commands- 

Note-
* any stack name could be used. e.g. `dev`
* use your preferred AWS region. e.g. `eu-west-2`
* the pulumi organisation could be the name of the individual's account. It's needed when retrieving stack outputs from other sub-projects.
* 'gateway' sub-project also needs `pulumi config set ec2_keypair_name xxxx` where xxxx is the name of an already active key pair.
* 'gateway' sub-project also needs `export GATEWAY_HTTP_PASSWORD=supersecret` replace `supersecret` with your password.

```shell
export PULUMI_ORGANISATION=xxxxxx
pulumi stack init dev
pulumi config set aws:region eu-west-2
./go.sh dev
```

Point a web browser at the gateway's ip address, use 'http', not 'https'. The username will be 'fossa' and the password will be whatever you exported into `GATEWAY_HTTP_PASSWORD`.

## Clean-up

To tidy up and delete all the resources when you are done go into the sub-directoy for each sub-project in reverse order and run-

```
pulumi destroy
```
