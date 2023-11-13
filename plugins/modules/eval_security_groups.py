#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: eval_security_groups
short_description: Evaluate ingress and egress security group rules
description:
  - Evaluates ingress and egress security group rules.
  - Confirms whether the security group rules allow the needed traffic between the source and destination resources.
author:
  - Alina Buzachis (@alinabuzachis)
options:
  src_ip:
    description:
    - The private IPv4 address of the AWS resource in your Amazon VPC you want to test connectivity from.
    type: str
    required: true
  src_security_groups:
    description:
    - Destination Security Groups.
    type: list
    elements: str
    required: true
  dst_ip:
    description:
    - The IPv4 address of the resource you want to connect to.
    type: str
    required: true
  dst_port:
    description:
    - The port number you want to connect to on the destination resource.
    type: int
    required: true
  dst_security_groups:
    description:
    - Destination Security Groups.
    type: list
    elements: str
    required: true
  security_groups:
    description:
    - Security Groups.
    type: list
    elements: dict
    required: true
"""


EXAMPLES = r"""
- name: Evaluate ingress and egress security group rules
  cloud.aws_troubleshooting.eval_security_groups:
    src_ip: "172.32.1.31"
    src_security_groups:
      - "sg-0258afe8541042bac"
    dst_ip: "172.32.2.13"
    dst_port: 3389
    dst_security_groups:
      - "sg-05f6695f90530a499"
    security_groups:
      - description: "security group for jumphosts within the public subnet of ansible VPC"
        group_id: "sg-0258afe8541042bac"
        group_name: "sg_ansibleVPC_publicsubnet_jumphost"
        ip_permissions:
          - from_port: 3389
            ip_protocol: "tcp"
            ip_ranges:
              - cidr_ip: "0.0.0.0/0"
                description: "allow rdp to jumphost"
            ipv6_ranges: []
            prefix_list_ids: []
            to_port: 3389
            user_id_group_pairs: []
        ip_permissions_egress:
          - ip_protocol: "-1"
            ip_ranges:
              - cidr_ip: "0.0.0.0/0"
            ipv6_ranges: []
            prefix_list_ids: []
            user_id_group_pairs: []
        owner_id: "721066863947"
        tags: {}
        vpc_id: "vpc-097bb89457aa6d8f3"
      - description: "security group for private subnet that allows limited access from public subnet"
        group_id: "sg-05f6695f90530a499"
        group_name: "sg_ansibleVPC_privatesubnet_servers"
        ip_permissions:
          - from_port: 3389
            ip_protocol: "tcp"
            ip_ranges: []
            ipv6_ranges: []
            prefix_list_ids: []
            to_port: 3389
            user_id_group_pairs:
              - description: "allow only rdp access from public to private subnet servers"
                group_id: "sg-0258afe8541042bac"
                user_id: "721066863947"
        ip_permissions_egress:
          - ip_protocol: "-1"
            ip_ranges:
              - cidr_ip: "0.0.0.0/0"
            ipv6_ranges: []
            prefix_list_ids: []
            user_id_group_pairs: []
        owner_id: "721066863947"
        tags: {}
        vpc_id: "vpc-097bb89457aa6d8f3"
"""


RETURN = r"""
result:
  type: str
  description: Results from evaluating ingress and egress security group rules.
  returned: success
  sample: 'Security Groups rules evaluation successful'
"""


from ipaddress import ip_address, ip_network

from ansible.module_utils.basic import AnsibleModule


class EvalSecurityGroups(AnsibleModule):
    def __init__(self):
        argument_spec = dict(
            src_ip=dict(type="str", required=True),
            src_security_groups=dict(type="list", elements="str", required=True),
            dst_ip=dict(type="str", required=True),
            dst_port=dict(type="int", required=True),
            dst_security_groups=dict(type="list", elements="str", required=True),
            security_groups=dict(type="list", elements="dict", required=True),
        )

        super(EvalSecurityGroups, self).__init__(argument_spec=argument_spec)

        for key in argument_spec:
            setattr(self, key, self.params.get(key))

        self.execute_module()

    def eval_sg_rules(self):
        src_ip = ip_address(self.src_ip)
        dst_ip = ip_address(self.dst_ip)
        dst_port = int(self.dst_port)

        def eval_src_egress_rules():
            for src_security_group in self.src_security_groups:
                sg = [group for group in self.security_groups if group["group_id"] == src_security_group][0]
                for rule in sg["ip_permissions_egress"]:
                    if (
                        (rule.get("ip_protocol") == "-1")
                        or (rule.get("from_port") == -1 and rule.get("to_port") == -1)
                        or (dst_port in range(rule.get("from_port"), rule.get("to_port") + 1))
                    ):
                        for cidr in rule["ip_ranges"]:
                            if dst_ip in ip_network(cidr["cidr_ip"], strict=False):
                                return True
                        for group in rule["user_id_group_pairs"]:
                            if any(sg in group["group_id"] for sg in self.dst_security_groups):
                                return True
            self.fail_json(
                msg="Egress rules on source do not allow traffic towards destination: {0} : {1}".format(
                    self.dst_ip, str(dst_port)
                )
            )

        def eval_dst_ingress_rules():
            for dst_security_group in self.dst_security_groups:
                sg = [group for group in self.security_groups if group["group_id"] == dst_security_group][0]
                for rule in sg["ip_permissions"]:
                    if (
                        (rule.get("ip_protocol") == "-1")
                        or (rule.get("from_port") == -1 and rule.get("to_port") == -1)
                        or (dst_port in range(rule.get("from_port"), rule.get("to_port") + 1))
                    ):
                        for cidr in rule["ip_ranges"]:
                            if src_ip in ip_network(cidr["cidr_ip"], strict=False):
                                return True
                        for group in rule["user_id_group_pairs"]:
                            if any(sg in group["group_id"] for sg in self.src_security_groups):
                                return True
            self.fail_json(
                msg="Ingress rules on destination do not allow traffic from source: {0} towards destination port {1}".format(
                    self.src_ip, str(dst_port)
                )
            )

        eval_src_egress_rules()
        eval_dst_ingress_rules()

        return True

    def check_src_egress_rules(self):
        dst_ip = ip_address(self.dst_ip)
        dst_port = int(self.dst_port)

        for sg_id in self.src_security_groups:
            sg = [group for group in self.security_groups if group["group_id"] == sg_id][0]
            for rule in sg["ip_permissions_egress"]:
                if (
                    (rule.get("ip_protocol") == "-1")
                    or (rule.get("from_port") == -1 and rule.get("to_port") == -1)
                    or (dst_port in range(rule.get("from_port"), rule.get("to_port") + 1))
                ):
                    for cidr in rule["ip_ranges"]:
                        if dst_ip in ip_network(cidr["cidr_ip"], strict=False):
                            return True
        self.fail_json(
            msg="Egress rules on source do not allow traffic towards destination: {0} : {1}".format(
                self.dst_ip, str(dst_port)
            )
        )

    def execute_module(self):
        try:
            # Evaluate Ingress and Egress security groups rules
            self.check_src_egress_rules()
            self.eval_sg_rules()
            self.exit_json(result="Security Groups rules validation successful")
        except Exception as e:
            self.fail_json(msg="Security Groups rules validation failed: {0}".format(e))


def main():
    EvalSecurityGroups()


if __name__ == "__main__":
    main()
