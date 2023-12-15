// Copyright (c) 2021, 2022, Oracle and/or its affiliates.


#######################################
# Resource Block - Network Load Balancer
# Create Network Load Balancer
#######################################

resource "oci_network_load_balancer_network_load_balancer" "network_load_balancer" {
  #Required
  compartment_id                 = var.compartment_id
  display_name                   = var.display_name
  subnet_id                      = var.subnet_id
  is_preserve_source_destination = var.is_preserve_source_destination
  is_private                     = var.is_private
  network_security_group_ids     = var.network_security_group_ids != null ? (local.nsg_ids == [] ? ["INVALID NSG Name"] : local.nsg_ids) : null
  nlb_ip_version                 = var.nlb_ip_version
  defined_tags                   = var.defined_tags
  freeform_tags                  = var.freeform_tags

  dynamic "reserved_ips" {
    for_each = var.reserved_ips_id != [] ? var.reserved_ips_id : []
    content {
      #Optional
      id = reserved_ips.value
    }
  }
  lifecycle {
    ignore_changes = [reserved_ips]
  }
}
