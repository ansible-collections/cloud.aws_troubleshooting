connectivity_troubleshooter
=========

A role to troubleshoot connectivity issues between the following:

- AWS resources within an Amazon Virtual Private Cloud (Amazon VPC);
- AWS resources in different Amazon VPCs within the same AWS Region that are connected using VPC peering;
- AWS resources in an Amazon VPC and an internet resource using an internet gateway;
- AWS resources in an Amazon VPC and an internet resource using a network address translation (NAT) gateway.

This role does not perform connectivity tests directly, rather it retrieves information about the resources, security groups, network ACLs, and route tables to verify that the source and destination are configured correctly.

Requirements
------------

Authentication against AWS is managed by the `aws_setup_credentials` role.

It also requires the folllowing roles:

- cloud.aws_troubleshooting.connectivity_troubleshooter_validate
- cloud.aws_troubleshooting.connectivity_troubleshooter_igw
- cloud.aws_troubleshooting.connectivity_troubleshooter_local
- cloud.aws_troubleshooting.connectivity_troubleshooter_nat
- cloud.aws_troubleshooting.connectivity_troubleshooter_peering

Role Variables
--------------

- **connectivity_troubleshooter_destination_ip**: (Required) The IPv4 address of the resource you want to connect to.
- **connectivity_troubleshooter_destination_port**: (Required) The port number you want to connect to on the destination resource.
- **connectivity_troubleshooter_destination_vpc**: (Optional) The ID of the Amazon VPC you want to test connectivity to.
- **connectivity_troubleshooter_source_ip**: (Required) The private IPv4 address of the AWS resource in your Amazon VPC you want to test connectivity from.
- **connectivity_troubleshooter_source_port_range**: (Optional) The port range used by the AWS resource in your Amazon VPC you want to test connectivity from.
- **connectivity_troubleshooter_source_vpc**: (Optional) The ID of the Amazon VPC you want to test connectivity from.

Dependencies
------------

- role: aws_setup_credentials

Example Playbook
----------------

```yaml
---
- name: AWS connectivity_troubleshooter example
  hosts: localhost

  roles:
    - role: cloud.aws_troubleshooting.connectivity_troubleshooter
      connectivity_troubleshooter_destination_ip: 172.31.2.8
      connectivity_troubleshooter_destination_port: 443
      connectivity_troubleshooter_source_ip: 172.31.2.7
```

License
-------

GNU General Public License v3.0 or later

See [LICENSE](https://github.com/redhat-cop/cloud.aws_troubleshooting/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
