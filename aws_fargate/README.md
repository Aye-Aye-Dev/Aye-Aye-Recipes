# AWS Fargate

Run loads of [Fossa](https://github.com/Aye-Aye-Dev/Fossa) workers in [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) containers so the subtasks in an Aye-Aye partitioned ETL model can be run in parallel across a distributed cluster.

## Key technologies used in this recipe

* [Pulumi](https://www.pulumi.com/) as the orchestrator. Pulumi is like Terraform but easier to engage and work with.
* [Ansible](https://www.ansible.com/) to provision the EC2 instance (because [`pulumi_command`](https://www.pulumi.com/registry/packages/command/) doesn't look quite ready)
* [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) - Containers without the complexity of Kubernetes or provisioning EC2 instances.


## Decision log

It's an opiniated stack so has been split into sub-modules (detailed below). Here is the background on these opiniated decisions-

* *Gateway EC2 instance* - I really really don't want public IP addresses on each task in the cluster. In part because they incur a cost but also because private IPs are slightly safer in terms of security. I want to use AWS' [ECR](https://aws.amazon.com/ecr/) (Elastic Container Registry) with [ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html) but in order to fetch images this requires a network transit to a public IP address. The obvious solution is to use a NAT gateway but a less resiliant and less expensive alternative is to use an EC2 instance for NAT. The NAT functionality of the gateway has to use EC2 is because containers in ECS can't have the [source/destination check](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-networking-awsvpc.html) disabled on the ENI. 

* Because an EC2 instance is being used for NAT it has a public IP address so can be used to access containers in the cluster. The [fossa gateway app](./gateway/apps/fossa_gateway) is a small flask app to give a view of containers and their tasks. This app could be run within a container if there is another route to it. e.g. a VPN, a public load balancer, a public IP address etc.

* Build host - the docker images could be built locally and pushed up but I prefer the CI/CD style of having a build host. The gateway EC2 instance does this. The ansible playbook does the building and pushing to ECR.

* There aren't any TLS certificates in this example but there is basic HTTP authentication. If there was TLS I would have made it possible to post new tasks to the cluster from the Gateway.


## Running this

Run the 'Usage' section from the [top level README](../README.md) to setup the Python environment needed to run the devops commands.

First, [setup Pulumi](https://www.pulumi.com/docs/get-started/).

The orchestration and provisioning has been split into sub-projects. This will make it easier to pick and choose from my opiniated stack. There are 3 sub-projects which each have a corresponding sub-directory-

* networks
* gateway
* cluster

### TLDR;

Run the `go.sh` script in each directory in the order they are listed above.


### Slightly longer

The first time you run this, setup a Pulumi stack for each sub-project-

```shell
cd networks
pulumi stack init dev
pulumi config set aws:region eu-west-2
cd ../gateway
pulumi stack init dev
pulumi config set aws:region eu-west-2
pulumi config set ec2_keypair_name xxxx
cd ../cluster
pulumi stack init dev
pulumi config set aws:region eu-west-2
cd ..
```

Note-
* any stack name could be used. e.g. `dev`
* use your preferred AWS region. e.g. `eu-west-2`
* 'gateway' sub-project also needs `pulumi config set ec2_keypair_name xxxx` where xxxx is the name of an already active key pair.


From there on, just the `go.sh` script with a few environmental variables is needed to standup each sub-project-

```shell
export GATEWAY_HTTP_PASSWORD=supersecret
export PULUMI_ORGANISATION=xxxxxx

cd networks
./go.sh dev
cd ../gateway
./go.sh dev
cd ../cluster
./go.sh dev
```

Note-
* the pulumi organisation could be the name of a Pulumi organisation or the individual's account (i.e. the Pulumi user's account). It's needed when retrieving stack outputs from other sub-projects.
* For `export GATEWAY_HTTP_PASSWORD=supersecret` replace `supersecret` with your password.


The gateway's `public_ip` address is one of the pulumi `Outputs` at the end of the *gateway* sub-project.

Point a web browser at the gateway's ip address (this is the, use 'http', not 'https'. The username will be 'fossa' and the password will be whatever you exported into `GATEWAY_HTTP_PASSWORD`.


## Running a task

Pointing a brower at the gateway will list running tasks. A task in this context is a docker container running in ECS.

For the security related reason detailed in the decision log above, it's not possible to post a task to the gateway's web interface. For now, ssh into the gateway (use `cd gateway; ssh ubuntu@`pulumi stack output public_ip`) and use curl. Replace the IP address in this curl command with that of any running task.


```shell
curl --header "Content-Type: application/json" \
     --data '{"model_class":"PartitionedExampleEtl"}'  \
     --request POST http://192.168.0.0:2345/api/0.01/task
```

Viewing each task in the Gateway's listing will show details of subtasks run on each fossa node (i.e. by each ECS task).


## Clean-up

Delete all the container images in the Elastic Container Registry.

To tidy up and delete all the resources when you are done go into the sub-directoy for each sub-project in reverse order and run-

```
pulumi destroy
```
