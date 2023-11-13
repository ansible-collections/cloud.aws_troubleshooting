#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: eval_network_acls
short_description: Evaluate ingress and egress network ACLs
description:
  - Evaluate ingress and egress network ACLs.
author:
  - Alina Buzachis (@alinabuzachis)
options:
  src_ip:
    description:
    - The private IPv4 address of the AWS resource in your Amazon VPC you want to test connectivity from.
    type: str
    required: true
  src_subnet_id:
    description:
    - Source Subnet id.
    type: str
    required: true
  src_port_range:
    description:
    - The port range used by the AWS resource in your Amazon VPC you want to test connectivity from.
    type: str
    required: false
  dst_ip:
    description:
    - The IPv4 address of the resource you want to connect to.
    type: str
    required: true
  dst_port:
    description:
    - The port number you want to connect to on the destination resource.
    type: str
    required: true
  dst_subnet_id:
    description:
    - Destination Subnet id.
    type: str
    required: true
  src_network_acls:
    description:
    - Source Network ACL Rules.
    type: list
    elements: dict
    required: true
  dst_network_acls:
    description:
    - Destination Network ACL Rules.
    type: list
    elements: dict
    required: true
"""


EXAMPLES = r"""
- name: Evaluate ingress and egress network ACLs
  cloud.aws_troubleshooting.eval_network_acls:
    src_ip: "172.32.1.31"
    src_subnet_id: "subnet-0d8ddbeaa790da839"
    dst_ip: "172.32.2.13"
    dst_port: 3389
    dst_subnet_id: "subnet-06cc4582cb0dde318"
    # Network ACL entries order
    # ["rule_number", "protocol", "rule_action", "cidr_block", "icmp_type", "icmp_code", "port_from", "port_to"]
    src_network_acls:
      - egress:
          - - 100
            - "all"
            - "allow"
            - "0.0.0.0/0"
            - null
            - null
            - 0
            - 65535
      - ingress:
          - - 100
            - "all"
            - "allow"
            - "0.0.0.0/0"
            - null
            - null
            - 0
            - 65535
    dst_network_acls:
      - egress:
          - - 100
            - "all"
            - "allow"
            - "0.0.0.0/0"
            - null
            - null
            - 0
            - 65535
      - ingress:
          - - 100
            - "all"
            - "allow"
            - "0.0.0.0/0"
            - null
            - null
            - 0
            - 65535
"""


RETURN = r"""
result:
  type: str
  description: Results from evaluating ingress and egress network ACLs.
  returned: success
  sample: 'Network ACLs evaluation successful'
"""


from ipaddress import ip_address, ip_network

from ansible.module_utils.basic import AnsibleModule


class EvalNetworkAcls(AnsibleModule):
    def __init__(self):
        argument_spec = dict(
            src_ip=dict(type="str", required=True),
            src_subnet_id=dict(type="str", required=True),
            src_port_range=dict(type="str", required=False),
            dst_ip=dict(type="str", required=True),
            dst_subnet_id=dict(type="str", required=True),
            dst_port=dict(type="str", required=True),
            src_network_acls=dict(type="list", elements="dict", required=True),
            dst_network_acls=dict(type="list", elements="dict", required=True),
        )

        super(EvalNetworkAcls, self).__init__(argument_spec=argument_spec)

        for key in argument_spec:
            setattr(self, key, self.params.get(key))

        self.execute_module()

    def eval_nacls(self):
        src_port_from = None
        src_port_to = None
        # entry list format
        keys = [
            "rule_number",
            "protocol",
            "rule_action",
            "cidr_block",
            "icmp_type",
            "icmp_code",
            "port_from",
            "port_to",
        ]
        if self.src_port_range:
            src_port_from = int(self.src_port_range.split("-")[0])
            src_port_to = int(self.src_port_range.split("-")[1])
        src_ip = ip_address(self.src_ip)
        dst_ip = ip_address(self.dst_ip)
        dst_port = int(self.dst_port)

        if self.src_subnet_id == self.dst_subnet_id:
            return True

        def eval_src_nacls(acls):
            def check_egress_acls(acls, dst_ip, dst_port):
                for item in acls:
                    acl = dict(zip(keys, item))
                    # Check ipv4 acl rule only
                    if acl.get("cidr_block"):
                        # Check IP
                        if dst_ip in ip_network(acl["cidr_block"], strict=False):
                            # Check Port
                            if (acl.get("protocol") == "all") or (
                                dst_port
                                in range(
                                    acl["port_from"],
                                    acl["port_to"] + 1,
                                )
                            ):
                                # Check Action
                                if acl["rule_action"] == "allow":
                                    return True
                                else:
                                    self.fail_json(
                                        msg=f"Source Subnet Network Acl Egress Rules do not allow outbound traffic to destination: {0} : {1}".format(
                                            self.dst_ip, str(dst_port)
                                        )
                                    )

                self.fail_json(
                    msg="Source Subnet Network Acl Egress Rules do not allow outbound traffic to destination: {0} : {1}".format(
                        self.dst_ip, str(dst_port)
                    )
                )

            def check_ingress_acls(acls, src_ip):
                for item in acls:
                    acl = dict(zip(keys, item))
                    # Check ipv4 acl rule only
                    if acl.get("cidr_block"):
                        # Check IP
                        if src_ip in ip_network(acl["cidr_block"], strict=False):
                            # Check Port
                            if (acl.get("protocol") == "all") or (
                                src_port_from
                                and src_port_to
                                and set(range(src_port_from, src_port_to)).issubset(
                                    range(
                                        acl["port_from"],
                                        acl["port_to"] + 1,
                                    )
                                )
                            ):
                                # Check Action
                                if acl["rule_action"] == "allow":
                                    return True
                                else:
                                    self.fail_json(
                                        msg="Source Subnet Network Acl Ingress Rules do not allow inbound traffic from destination: {0}".format(
                                            self.dst_ip
                                        )
                                    )

                self.fail_json(
                    msg="Source Subnet Network Acl Ingress Rules do not allow inbound traffic from destination: {0}".format(
                        self.dst_ip
                    )
                )

            egress_acls = [acl["egress"] for acl in acls if acl["egress"]][0]
            ingress_acls = [acl["ingress"] for acl in acls if acl["ingress"]][0]

            src_egress_check_pass = check_egress_acls(egress_acls, dst_ip, dst_port)
            src_ingress_check_pass = check_ingress_acls(ingress_acls, dst_ip)

            if src_ingress_check_pass and src_egress_check_pass:
                return True

        def eval_dst_nacls(acls):
            def check_egress_acls(acls, dst_ip):
                for item in acls:
                    acl = dict(zip(keys, item))
                    # Check ipv4 acl rule only
                    if acl.get("cidr_block"):
                        # Check IP
                        if dst_ip in ip_network(acl["cidr_block"], strict=False):
                            # Check Port
                            if (acl.get("protocol") == "all") or (
                                src_port_from
                                and src_port_to
                                and set(range(src_port_from, src_port_to)).issubset(
                                    range(
                                        acl["port_from"],
                                        acl["port_to"] + 1,
                                    )
                                )
                            ):
                                # Check Action
                                if acl["rule_action"] == "allow":
                                    break
                                else:
                                    self.fail_json(
                                        msg="Destination Subnet Network Acl Egress Rules do not allow outbound traffic to source: {0}".format(
                                            self.src_ip
                                        )
                                    )
                self.fail_json(
                    msg="Destination Subnet Network Acl Egress Rules do not allow outbound traffic to source: {0}".format(
                        self.src_ip
                    )
                )

            def check_ingress_acls(acls, src_ip, dst_port):
                for item in acls:
                    acl = dict(zip(keys, item))
                    # Check ipv4 acl rule only
                    if acl.get("cidr_block"):
                        # Check IP
                        if src_ip in ip_network(acl["cidr_block"], strict=False):
                            # Check Port
                            if (acl.get("protocol") == "all") or (
                                dst_port
                                in range(
                                    acl["port_from"],
                                    acl["port_to"] + 1,
                                )
                            ):
                                # Check Action
                                if acl["rule_action"] == "allow":
                                    return True
                                else:
                                    self.fail_json(
                                        msg="Destination Subnet Network Acl Ingress Rules do not allow inbound traffic from source: {0} \
                                            towards destination port {1}".format(
                                            self.src_ip, str(self.dst_port)
                                        )
                                    )

                self.fail_json(
                    msg="Destination Subnet Network Acl Ingress Rules do not allow inbound traffic from source: {0} towards destination port {1}".format(
                        self.src_ip, str(self.dst_port)
                    )
                )

            egress_acls = [acl["egress"] for acl in acls if acl["egress"]][0]
            ingress_acls = [acl["ingress"] for acl in acls if acl["ingress"]][0]

            dst_ingress_check_pass = check_ingress_acls(ingress_acls, src_ip, dst_port)
            dst_egress_check_pass = check_egress_acls(egress_acls, src_ip)

            if dst_ingress_check_pass and dst_egress_check_pass:
                return True

        eval_src_nacls(self.src_network_acls)
        eval_dst_nacls(self.dst_network_acls)

        return True

    def execute_module(self):
        try:
            # Evaluate Ingress and Egress network ACLs
            self.eval_nacls()
            self.exit_json(result="Network ACLs evaluation successful")
        except Exception as e:
            self.fail_json(msg="Network ACLs evaluation failed: {0}".format(e))


def main():
    EvalNetworkAcls()


if __name__ == "__main__":
    main()
