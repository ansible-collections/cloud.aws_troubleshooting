troubleshoot_rds_connectivity
==================

A role to troubleshoot RDS connectivity from an EC2 instance.

The role diagnoses connectivity issues between an EC2 instance and an Amazon Relational Database Service instance, ensures the DB instance is available, and then checks the associated security group rules, network access control lists (network ACLs), and route tables for potential connectivity issues.

Requirements
------------

N/A

Role Variables
--------------

* **troubleshoot_rds_connectivity_db_instance_id**: (Required) The DB instance ID to test connectivity to.
* **troubleshoot_rds_connectivity_ec2_instance_id**: (Required) The ID of the EC2 instance to test connectivity from.

Dependencies
------------

* role: aws_setup_credentials

Example Playbook
----------------

```yaml
- hosts: localhost

  roles:
    - role: cloud.aws_troubleshooting.troubleshoot_rds_connectivity
      troubleshoot_rds_connectivity_db_instance_id: my-db_instance_id
      troubleshoot_rds_connectivity_ec2_instance_id: ec2-instance-dx
```

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.aws_troubleshooting/blob/main/LICENSE) to see the full text.

Author Information
------------------

* Ansible Cloud Content Team
