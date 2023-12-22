#!/usr/bin/python3

import sys
import oci
from oci.core.virtual_network_client import VirtualNetworkClient
import os
from .exportRoutetable import export_routetable
from .exportRoutetable import export_drg_routetable
from .exportSeclist import export_seclist
from .exportNSG import export_nsg

sys.path.append(os.getcwd() + "/..")
from commonTools import *

importCommands = {}
importCommands_rpc = {}
importCommands_vlan = {}
oci_obj_names = {}


def print_drgv2(values_for_column_drgv2, region, comp_name, vcn_info, drg_info, drg_attachment_info, drg_rt_info,
                import_drg_route_distribution_info, drg_route_distribution_statements):
    for col_header in values_for_column_drgv2.keys():
        if (col_header == "Region"):
            values_for_column_drgv2[col_header].append(region)
        elif (col_header == "Compartment Name"):
            values_for_column_drgv2[col_header].append(comp_name)
        elif (col_header == "DRG Name"):
            values_for_column_drgv2[col_header].append(drg_info.display_name)
        elif (col_header == "Attached To"):
            if (drg_attachment_info is None):
                values_for_column_drgv2[col_header].append('')
            else:
                if (drg_attachment_info.network_details is not None):
                    attach_type = drg_attachment_info.network_details.type
                    attach_id = drg_attachment_info.network_details.id
                # DRG v1
                else:
                    attach_type = "VCN"
                    attach_id = drg_attachment_info.vcn_id

                if (attach_type.upper() == "VCN"):
                    columnval = attach_type + "::" + vcn_info.display_name
                    values_for_column_drgv2[col_header].append(columnval)
                else:
                    columnval = attach_type + "::" + attach_id
                    values_for_column_drgv2[col_header].append(columnval)

        elif (col_header == "DRG RT Name"):
            if (drg_rt_info == None):
                values_for_column_drgv2[col_header].append("")
            else:
                values_for_column_drgv2[col_header].append(drg_rt_info.display_name)
        elif (col_header == 'Import DRG Route Distribution Name'):
            if import_drg_route_distribution_info == None:
                values_for_column_drgv2[col_header].append("")
            else:
                values_for_column_drgv2[col_header].append(import_drg_route_distribution_info.display_name)
        elif (col_header == "Import DRG Route Distribution Statements"):
            statement_val = ''
            if (drg_route_distribution_statements == None):
                statement_val = ''
            else:
                for stmt in drg_route_distribution_statements.data:
                    priority = stmt.priority
                    if (len(stmt.match_criteria)) != 0:
                        match_type = stmt.match_criteria[0].match_type
                        if (match_type == "DRG_ATTACHMENT_TYPE"):
                            attachment_type = stmt.match_criteria[0].attachment_type
                            statement_val = statement_val + "\n" + match_type + "::" + attachment_type + "::" + str(
                                priority)
                        elif (match_type == "DRG_ATTACHMENT_ID"):
                            drg_attachment_id = stmt.match_criteria[0].drg_attachment_id
                            statement_val = statement_val + "\n" + match_type + "::" + drg_attachment_id + "::" + str(
                                priority)
                        elif (match_type == "MATCH_ALL"):
                            statement_val = statement_val + "\n" + match_type + "::" + "::" + str(priority)
                    else:
                        statement_val = statement_val + "\n" + "ALL::::" + str(priority) + "\n"
            values_for_column_drgv2[col_header].append(statement_val)
        elif col_header.lower() in commonTools.tagColumns:
            values_for_column_drgv2 = commonTools.export_tags(drg_info, col_header, values_for_column_drgv2)
        else:
            oci_objs = [drg_info, drg_attachment_info, drg_rt_info, import_drg_route_distribution_info]
            values_for_column_drgv2 = commonTools.export_extra_columns(oci_objs, col_header, sheet_dict_drgv2,
                                                                       values_for_column_drgv2)


def print_vcns(values_for_column_vcns, region, comp_name, vcn_info, drg_info, igw_info, ngw_info, sgw_info,
               lpg_display_names):
    for col_header in values_for_column_vcns.keys():
        if (col_header == "Region"):
            values_for_column_vcns[col_header].append(region)
        elif (col_header == "Compartment Name"):
            values_for_column_vcns[col_header].append(comp_name)
        elif (col_header == "DRG Required"):
            if (drg_info == None):
                values_for_column_vcns[col_header].append("n")
            else:
                values_for_column_vcns[col_header].append(drg_info.display_name)

        elif (col_header == "IGW Required"):
            if (igw_info == None):
                values_for_column_vcns[col_header].append("n")
            else:
                values_for_column_vcns[col_header].append(igw_info.display_name)
        elif (col_header == "NGW Required"):
            if (ngw_info == None):
                values_for_column_vcns[col_header].append("n")
            else:
                values_for_column_vcns[col_header].append(ngw_info.display_name)
        elif (col_header == "SGW Required"):
            if (sgw_info == None):
                values_for_column_vcns[col_header].append("n")
            else:
                values_for_column_vcns[col_header].append(sgw_info.display_name)
        elif (col_header == "LPG Required"):
            values_for_column_vcns[col_header].append(lpg_display_names)
        elif (col_header == "DNS Label"):
            value = vcn_info.dns_label
            if value is None:
                values_for_column_vcns[col_header].append("n")
            else:
                values_for_column_vcns[col_header].append(value)
        elif (col_header == "Hub/Spoke/Peer/None"):
            values_for_column_vcns[col_header].append("exported")
        elif col_header.lower() in commonTools.tagColumns:
            values_for_column_vcns = commonTools.export_tags(vcn_info, col_header, values_for_column_vcns)
        else:
            oci_objs = [vcn_info, drg_info, igw_info, ngw_info, sgw_info]
            values_for_column_vcns = commonTools.export_extra_columns(oci_objs, col_header, sheet_dict_vcns,
                                                                      values_for_column_vcns)

    tf_name = commonTools.check_tf_variable(vcn_info.display_name)
    importCommands[region.lower()].write(
        "\nterraform import \"module.vcns[\\\"" + tf_name + "\\\"].oci_core_vcn.vcn\" " + str(vcn_info.id))


def print_dhcp(values_for_column_dhcp, region, comp_name, vcn_name, dhcp_info):
    tf_name = vcn_name + "_" + str(dhcp_info.display_name)
    tf_name = commonTools.check_tf_variable(tf_name)

    options = dhcp_info.options
    server_type = ""
    custom_dns_servers_str = ""
    search_domain_names_str = ""
    oci_objs = [dhcp_info]
    for option in options:
        oci_objs.append(option)
        if (option.type == "DomainNameServer"):
            server_type = option.server_type
            custom_dns_servers = option.custom_dns_servers
            for custom_dns_server in custom_dns_servers:
                custom_dns_servers_str = custom_dns_servers_str + "," + custom_dns_server
            if (custom_dns_servers_str != "" and custom_dns_servers_str[0] == ','):
                custom_dns_servers_str = custom_dns_servers_str[1:]
        if (option.type == "SearchDomain"):
            search_domain_names = option.search_domain_names
            search_domain_names_str = search_domain_names[0]

    for col_header in values_for_column_dhcp.keys():
        if (col_header == "Region"):
            values_for_column_dhcp[col_header].append(region)
        elif (col_header == "Compartment Name"):
            values_for_column_dhcp[col_header].append(comp_name)
        elif (col_header == "VCN Name"):
            values_for_column_dhcp[col_header].append(vcn_name)
        elif (col_header == "Server Type(VcnLocalPlusInternet|CustomDnsServer)"):
            values_for_column_dhcp[col_header].append(server_type)
        elif (col_header == "Search Domain"):
            values_for_column_dhcp[col_header].append(search_domain_names_str)
        elif (col_header == "Custom DNS Server"):
            values_for_column_dhcp[col_header].append(custom_dns_servers_str)
        elif col_header.lower() in commonTools.tagColumns:
            values_for_column_dhcp = commonTools.export_tags(dhcp_info, col_header, values_for_column_dhcp)
        else:
            values_for_column_dhcp = commonTools.export_extra_columns(oci_objs, col_header, sheet_dict_dhcp,
                                                                      values_for_column_dhcp)
    if ("Default DHCP Options for " in dhcp_info.display_name):
        importCommands[region.lower()].write(
            "\nterraform import \"module.default-dhcps[\\\"" + tf_name + "\\\"].oci_core_default_dhcp_options.default_dhcp_option\" " + str(
                dhcp_info.id))
    else:
        importCommands[region.lower()].write(
            "\nterraform import \"module.custom-dhcps[\\\"" + tf_name + "\\\"].oci_core_dhcp_options.custom_dhcp_option\" " + str(
                dhcp_info.id))


def print_subnets_vlans(values_for_column_subnets_vlans, region, comp_name, vcn_name, subnet_vlan_info, dhcp_name,
                        rt_name, sl_nsg_names, add_def_seclist, subnet_vlan_in_excel):
    tf_name = vcn_name + "_" + str(subnet_vlan_info.display_name)
    tf_name = commonTools.check_tf_variable(tf_name)
    if subnet_vlan_in_excel == 'Subnet':
        importCommands[region.lower()].write(
            "\nterraform import \"module.subnets[\\\"" + tf_name + "\\\"].oci_core_subnet.subnet\" " + str(
                subnet_vlan_info.id))
    elif subnet_vlan_in_excel == 'VLAN':
        importCommands_vlan[region.lower()].write(
            "\nterraform import \"module.vlans[\\\"" + tf_name + "\\\"].oci_core_vlan.vlan\" " + str(
                subnet_vlan_info.id))

    for col_header in values_for_column_subnets_vlans.keys():
        if (col_header == "Region"):
            values_for_column_subnets_vlans[col_header].append(region)
        elif (col_header == "Compartment Name"):
            values_for_column_subnets_vlans[col_header].append(comp_name)
        elif (col_header == "VCN Name"):
            values_for_column_subnets_vlans[col_header].append(vcn_name)
        elif (col_header == "Subnet or VLAN"):
            if subnet_vlan_in_excel == 'Subnet':
                values_for_column_subnets_vlans[col_header].append(subnet_vlan_in_excel)
            elif subnet_vlan_in_excel == 'VLAN':
                value = subnet_vlan_in_excel + "::" + str(subnet_vlan_info.vlan_tag)
                values_for_column_subnets_vlans[col_header].append(value)

        elif (col_header == "DHCP Option Name"):
            values_for_column_subnets_vlans[col_header].append(dhcp_name)
        elif (col_header == "Route Table Name"):
            values_for_column_subnets_vlans[col_header].append(rt_name)
        elif (col_header == "Seclist Names"):
            if subnet_vlan_in_excel == 'Subnet':
                values_for_column_subnets_vlans[col_header].append(sl_nsg_names)
            elif subnet_vlan_in_excel == 'VLAN':
                values_for_column_subnets_vlans[col_header].append("")
        elif (col_header == "NSGs"):
            if subnet_vlan_in_excel == 'Subnet':
                values_for_column_subnets_vlans[col_header].append("")
            elif subnet_vlan_in_excel == 'VLAN':
                values_for_column_subnets_vlans[col_header].append(sl_nsg_names)
        elif (col_header == "Add Default Seclist"):
            values_for_column_subnets_vlans[col_header].append(add_def_seclist)
        elif (col_header == "Configure SGW Route(n|object_storage|all_services)"):
            values_for_column_subnets_vlans[col_header].append("-")
        elif (col_header == "Configure NGW Route(y|n)"):
            values_for_column_subnets_vlans[col_header].append("-")
        elif (col_header == "Configure IGW Route(y|n)"):
            values_for_column_subnets_vlans[col_header].append("-")
        elif (col_header == "Configure OnPrem Route(y|n)"):
            values_for_column_subnets_vlans[col_header].append("-")
        elif (col_header == "Configure VCNPeering Route(y|n)"):
            values_for_column_subnets_vlans[col_header].append("-")
        elif ("Availability Domain" in col_header):
            value = subnet_vlan_info.__getattribute__(sheet_dict_subnets_vlans[col_header])
            ad = ""
            if (value == None):
                ad = "Regional"
            elif ("AD-1" in value.upper()):
                ad = "AD1"
            elif ("AD-2" in value.upper()):
                ad = "AD2"
            elif ("AD-3" in value.upper()):
                ad = "AD3"
            values_for_column_subnets_vlans[col_header].append(ad)
            # Get public or private
        elif (col_header == "Type(private|public)"):
            if subnet_vlan_in_excel == 'Subnet':
                value = subnet_vlan_info.__getattribute__(sheet_dict_subnets_vlans[col_header])
                if (value == True):
                    access = "private"
                elif (value == False):
                    access = "public"
            elif subnet_vlan_in_excel == 'VLAN':
                access = ""
            values_for_column_subnets_vlans[col_header].append(access)

        elif (col_header == "DNS Label"):
            if subnet_vlan_in_excel == 'Subnet':
                value = subnet_vlan_info.dns_label
                if value is None:
                    values_for_column_subnets_vlans[col_header].append("n")
                else:
                    values_for_column_subnets_vlans[col_header].append(value)
            elif subnet_vlan_in_excel == 'VLAN':
                values_for_column_subnets_vlans[col_header].append("")
        elif col_header.lower() in commonTools.tagColumns:
            values_for_column_subnets_vlans = commonTools.export_tags(subnet_vlan_info, col_header,
                                                                      values_for_column_subnets_vlans)
        else:
            oci_objs = [subnet_vlan_info]
            values_for_column_subnets_vlans = commonTools.export_extra_columns(oci_objs, col_header,
                                                                               sheet_dict_subnets_vlans,
                                                                               values_for_column_subnets_vlans)


def get_drg_rt_name(drg_rpc_attachment_list, source_rpc_id, rpc_source_client):
    for item in drg_rpc_attachment_list.data:
        if source_rpc_id == item.network_details.id:
            source_drg_rt_id = item.drg_route_table_id
            src_drg_rt_name = getattr(
                rpc_source_client.get_drg_route_table(drg_route_table_id=source_drg_rt_id).data,
                'display_name')
            return src_drg_rt_name, source_drg_rt_id


def get_rpc_resources(source_region, SOURCE_RPC_LIST, dest_rpc_dict, rpc_source_client, ct, values_for_column,
                      ntk_compartment_name, outdir):
    # Variables
    dest_rpc_drg_name = ""
    src_drg_rt_name = ""
    dest_drg_rt_name = ""
    drg_rt_import_dist_name = ""
    dest_drg_rt_import_dist_name = ""
    source_rpc_comp_name = ""
    dest_rpc_comp_name = ""
    dest_rpc_display_name = ""
    dest_import_rt_statements = None
    import_rt_statements = None
    rpc_safe_file = {}

    # set source region
    source_region = source_region

    def get_comp_details(comp_data):
        for c_name, c_id in ct.ntk_compartment_ids.items():
            if c_id == comp_data:
                return c_name

    # Get dict for columns from Excel_Columns
    sheet_dict = ct.sheet_dict["DRGs"]

    # creating rpc.safe file
    rpc_file = f'{outdir}/global/rpc/' + "rpc.safe"
    # Used against all regions to avoid duplicate entry
    rpc_safe_file["global"] = open(rpc_file, "a")

    # Fetch Source Data
    for new_rpc in SOURCE_RPC_LIST.data:
        source_rpc_id = new_rpc.id
        source_rpc_peer_id = new_rpc.peer_id

        # Check peering is alive
        if source_rpc_peer_id is not None and new_rpc.peering_status == "PEERED":
            source_rpc_comp_name = get_comp_details(new_rpc.compartment_id)
            source_rpc_display_name = new_rpc.display_name
            source_rpc_drg_id = new_rpc.drg_id
            dest_rpc_id = new_rpc.peer_id
            dest_region = new_rpc.peer_region_name.split("-")[1]
            source_rpc_drg_name = getattr(rpc_source_client.get_drg(drg_id=source_rpc_drg_id).data, 'display_name')
            rpc_tf_name = commonTools.check_tf_variable(new_rpc.display_name)

            # Fetch source attach list id
            drg_rpc_attachment_list = rpc_source_client.list_drg_attachments(compartment_id=ct.ntk_compartment_ids[
                ntk_compartment_name], attachment_type="REMOTE_PEERING_CONNECTION", drg_id=new_rpc.drg_id,
                                                                             lifecycle_state="ATTACHED")

            # Fetch source DRG RT name
            src_drg_rt_name, source_drg_rt_id = get_drg_rt_name(drg_rpc_attachment_list, source_rpc_id,
                                                                rpc_source_client)
            # Fetch source DRG import route distribution id, name
            src_drg_rt_dist = rpc_source_client.get_drg_route_table(drg_route_table_id=source_drg_rt_id)
            src_drg_rt_import_dist_id = getattr(src_drg_rt_dist.data, 'import_drg_route_distribution_id')
            if (src_drg_rt_import_dist_id!=None):
                import_rt_info = rpc_source_client.get_drg_route_distribution(drg_route_distribution_id=src_drg_rt_import_dist_id)
                drg_rt_import_dist_name = getattr(import_rt_info.data, "display_name")
                import_rt_statements = rpc_source_client.list_drg_route_distribution_statements(drg_route_distribution_id=src_drg_rt_import_dist_id)

            # Check for duplicate rpc entry in safe file first
            fo = open(f'{rpc_file}').read()
            # If existing RPC not present in safe file
            for region, client in dest_rpc_dict.items():
                if region == dest_region:
                    existing_line = f"{source_region.lower()},{region.lower()},{source_rpc_display_name},{source_rpc_peer_id}"
                    if existing_line in fo or source_rpc_id not in fo and source_rpc_peer_id not in fo:
                        if existing_line not in fo:
                            rpc_safe_file["global"].write(
                                f"{source_region.lower()},{region.lower()},{source_rpc_display_name},{source_rpc_peer_id} \n")

                        # get RPC data to get dest comp name
                        dest_rpc_comp_id = getattr(client.get_remote_peering_connection(remote_peering_connection_id=dest_rpc_id).data, "compartment_id")
                        # Fetch destination region data
                        new_client = oci.pagination.list_call_get_all_results(client.list_remote_peering_connections,
                                                                              compartment_id=dest_rpc_comp_id)

                        for dest_rpc in new_client.data:
                            if dest_rpc.id == source_rpc_peer_id:
                                dest_rpc_details = client.get_remote_peering_connection(
                                    remote_peering_connection_id=source_rpc_peer_id)
                                dest_rpc_drg_id = dest_rpc.drg_id
                                dest_rpc_drg_name = getattr(client.get_drg(drg_id=dest_rpc_drg_id).data, 'display_name')
                                dest_rpc_comp_name = get_comp_details(dest_rpc.compartment_id)
                                dest_rpc_display_name = dest_rpc.display_name
                                dest_drg_rpc_attachment_list = client.list_drg_attachments(
                                    compartment_id=dest_rpc_comp_id, attachment_type="REMOTE_PEERING_CONNECTION",
                                    drg_id=dest_rpc_drg_id)

                                for attachment in dest_drg_rpc_attachment_list.data:
                                    if dest_rpc_id == attachment.network_details.id:
                                        dest_attach_id = attachment.id

                                # Fetch Dest DRG RT name, id
                                if dest_drg_rpc_attachment_list.data:
                                    dest_drg_rt_name, dest_drg_rt_id = get_drg_rt_name(dest_drg_rpc_attachment_list,
                                                                                       dest_rpc_id, client)

                                    # Fetch source DRG import route distribution id, name
                                    dest_drg_rt_dist = client.get_drg_route_table(drg_route_table_id=dest_drg_rt_id)
                                    dest_drg_rt_import_dist_id = getattr(dest_drg_rt_dist.data,
                                                                         'import_drg_route_distribution_id')
                                    if dest_drg_rt_import_dist_id!=None:
                                        dest_import_rt_info = client.get_drg_route_distribution(drg_route_distribution_id=dest_drg_rt_import_dist_id)
                                        dest_drg_rt_import_dist_name = getattr(dest_import_rt_info.data, "display_name")
                                        dest_import_rt_statements = client.list_drg_route_distribution_statements(drg_route_distribution_id=dest_drg_rt_import_dist_id)

                                importCommands_rpc["global"].write(
                                    "\nterraform import \"module.rpcs[\\\"" + rpc_tf_name + f"\\\"].oci_core_remote_peering_connection.{source_region.lower()}_{region.lower()}_requester_rpc[\\\"region\\\"]\" " + str(
                                        source_rpc_id))
                                importCommands_rpc["global"].write(
                                    "\nterraform import \"module.rpcs[\\\"" + rpc_tf_name + f"\\\"].oci_core_remote_peering_connection.{source_region.lower()}_{region.lower()}_accepter_rpc[\\\"region\\\"]\" " + str(
                                        dest_rpc_id))

                        for col_header in values_for_column:
                            if col_header == 'Region':
                                values_for_column[col_header].append(source_region)
                            elif col_header == 'Attached To':
                                # Format is RPC::region::dest_rpc_comp_name::dest_rpc_drg_name
                                attach_to = "RPC::" + dest_region.lower() + "::" + dest_rpc_drg_name
                                values_for_column[col_header].append(attach_to)
                            elif col_header == 'Compartment Name':
                                values_for_column[col_header].append(source_rpc_comp_name)
                            elif col_header == 'RPC Display Name':
                                values_for_column[col_header].append(source_rpc_display_name)
                            elif col_header == 'DRG Name':
                                values_for_column[col_header].append(source_rpc_drg_name)
                            elif col_header == 'DRG RT Name':
                                values_for_column[col_header].append(src_drg_rt_name)
                            elif col_header == 'Import DRG Route Distribution Name':
                                values_for_column[col_header].append(drg_rt_import_dist_name)
                            elif col_header == "Import DRG Route Distribution Statements":
                                statement_val = ''
                                if import_rt_statements is None:
                                    statement_val = ''
                                else:
                                    for stmt in import_rt_statements.data:
                                        priority = stmt.priority
                                        if (len(stmt.match_criteria)) != 0:
                                            match_type = stmt.match_criteria[0].match_type
                                            if match_type == "DRG_ATTACHMENT_TYPE":
                                                attachment_type = stmt.match_criteria[0].attachment_type
                                                statement_val = statement_val + "\n" + match_type + "::" + attachment_type + "::" + str(
                                                    priority)
                                            elif match_type == "DRG_ATTACHMENT_ID":
                                                drg_attachment_id = stmt.match_criteria[0].drg_attachment_id
                                                statement_val = statement_val + "\n" + match_type + "::" + drg_attachment_id + "::" + str(
                                                    priority)
                                            elif match_type == "MATCH_ALL":
                                                statement_val = statement_val + "\n" + match_type + "::" + "::" + str(
                                                    priority)
                                        else:
                                            statement_val = statement_val + "\n" + "ALL::::" + str(priority) + "\n"
                                values_for_column[col_header].append(statement_val)

                            elif col_header.lower() in commonTools.tagColumns:
                                values_for_column = commonTools.export_tags(new_rpc, col_header, values_for_column)
                            else:
                                oci_objs = [new_rpc]
                                values_for_column = commonTools.export_extra_columns(oci_objs, col_header,
                                                                                     sheet_dict,
                                                                                     values_for_column)
                        # add target region entries to xl.should be ignored during create cal.
                        for col_header in values_for_column:
                            if col_header == 'Region':
                                values_for_column[col_header].append(dest_region.capitalize())
                            elif col_header == 'Attached To':
                                # Format is RPC::region::dest_rpc_comp_name::dest_rpc_drg_name
                                attach_to = "RPC::" + source_region.lower() + "::" + source_rpc_drg_name
                                values_for_column[col_header].append(attach_to)
                            elif col_header == 'Compartment Name':
                                values_for_column[col_header].append(dest_rpc_comp_name)
                            elif col_header == 'RPC Display Name':
                                values_for_column[col_header].append(dest_rpc_display_name)
                            elif col_header == 'DRG Name':
                                values_for_column[col_header].append(dest_rpc_drg_name)
                            elif col_header == 'DRG RT Name':
                                values_for_column[col_header].append(dest_drg_rt_name)
                            elif col_header == 'Import DRG Route Distribution Name':
                                values_for_column[col_header].append(dest_drg_rt_import_dist_name)
                            elif col_header == "Import DRG Route Distribution Statements":
                                statement_val = ''
                                if dest_import_rt_statements is None:
                                    statement_val = ''
                                else:
                                    for stmt in dest_import_rt_statements.data:
                                        priority = stmt.priority
                                        if (len(stmt.match_criteria)) != 0:
                                            match_type = stmt.match_criteria[0].match_type
                                            if match_type == "DRG_ATTACHMENT_TYPE":
                                                attachment_type = stmt.match_criteria[0].attachment_type
                                                statement_val = statement_val + "\n" + match_type + "::" + attachment_type + "::" + str(
                                                    priority)
                                            elif match_type == "DRG_ATTACHMENT_ID":
                                                drg_attachment_id = stmt.match_criteria[0].drg_attachment_id
                                                statement_val = statement_val + "\n" + match_type + "::" + drg_attachment_id + "::" + str(
                                                    priority)
                                            elif match_type == "MATCH_ALL":
                                                statement_val = statement_val + "\n" + match_type + "::" + "::" + str(
                                                    priority)
                                        else:
                                            statement_val = statement_val + "\n" + "ALL::::" + str(priority) + "\n"
                                values_for_column[col_header].append(statement_val)

                            elif col_header.lower() in commonTools.tagColumns:
                                values_for_column = commonTools.export_tags(new_rpc, col_header, values_for_column)
                            else:
                                oci_objs = [new_rpc]
                                values_for_column = commonTools.export_extra_columns(oci_objs, col_header,
                                                                                     sheet_dict,
                                                                                     values_for_column)
                        # print(values_for_column)
        else:
            continue

    # Close the safe_file post updates
    rpc_safe_file["global"].close()

def export_major_objects(inputfile, outdir, service_dir, config, signer, ct, export_compartments=[], export_regions=[]):
    global sheet_dict_vcns
    global sheet_dict_drgv2

    cd3file = inputfile
    if ('.xls' not in cd3file):
        print("\nAcceptable cd3 format: .xlsx")
        exit()

    # Read CD3
    df, values_for_column_vcns = commonTools.read_cd3(cd3file, "VCNs")
    df, values_for_column_drgv2 = commonTools.read_cd3(cd3file, "DRGs")

    # Get dict for columns from Excel_Columns
    sheet_dict_vcns = ct.sheet_dict["VCNs"]
    sheet_dict_drgv2 = ct.sheet_dict["DRGs"]

    print("Fetching VCN Major Objects...")

    # For RPCs import file.
    # Create backups
    rpc_file_name = 'tf_import_commands_' + "rpcs" + '_nonGF.sh'
    rpc_script_file = f'{outdir}/global/rpc/{rpc_file_name}'
    os.makedirs(os.path.dirname(rpc_script_file), exist_ok=True)
    importCommands_rpc["global"] = open(rpc_script_file, "w+")
    importCommands_rpc["global"].write("#!/bin/bash")
    importCommands_rpc["global"].write("\n")
    importCommands_rpc["global"].write("terraform init")
    importCommands_rpc["global"].write("\n\n######### Writing import for RPC #########\n\n")

    # Remove existing rpc.safe file if exists.
    file_path = f'{outdir}/global/rpc/' + "rpc.safe"
    if os.path.exists(file_path):
        os.remove(file_path)

    # Create backups
    for reg in export_regions:
        if (os.path.exists(outdir + "/" + reg + "/" + service_dir + "/tf_import_commands_network_major-objects_nonGF.sh")):
            commonTools.backup_file(outdir + "/" + reg + "/" + service_dir, "tf_import_network",
                                    "tf_import_commands_network_major-objects_nonGF.sh")
        if (os.path.exists(outdir + "/" + reg + "/" + service_dir + "/obj_names.safe")):
            commonTools.backup_file(outdir + "/" + reg + "/" + service_dir, "obj_names", "obj_names.safe")
        importCommands[reg] = open(
            outdir + "/" + reg + "/" + service_dir + "/tf_import_commands_network_major-objects_nonGF.sh", "w")
        importCommands[reg].write("#!/bin/bash")
        importCommands[reg].write("\n")
        importCommands[reg].write("terraform init")
        oci_obj_names[reg] = open(outdir + "/" + reg + "/" + service_dir + "/obj_names.safe", "w")

    print("Tabs- VCNs and DRGs would be overwritten during export process!!!\n")

    # Fetch DRGs
    for reg in export_regions:
        current_region = reg
        importCommands[reg].write("\n######### Writing import for DRGs #########\n")
        config.__setitem__("region", ct.region_dict[reg])
        vnc = VirtualNetworkClient(config=config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,signer=signer)
        region = reg.capitalize()
        drg_ocid = []
        drg_rt_ocid = []
        drg_comp_name = ''
        drg_version = "DRGv2"
        for ntk_compartment_name in export_compartments:
            DRG_Attachments = oci.pagination.list_call_get_all_results(vnc.list_drg_attachments,
                                                                       compartment_id=ct.ntk_compartment_ids[
                                                                           ntk_compartment_name],
                                                                       attachment_type="ALL")  # ,lifecycle_state ="ATTACHED")#,attachment_type="ALL")
            rpc_execution = True
            for drg_attachment_info in DRG_Attachments.data:
                if (drg_attachment_info.lifecycle_state != "ATTACHED"):
                    continue
                drg_attachment_name = drg_attachment_info.display_name
                drg_id = drg_attachment_info.drg_id
                drg_info = vnc.get_drg(drg_id).data

                # Attachment Data
                drg_display_name = drg_info.display_name
                drg_comp_id = drg_info.compartment_id
                for key, val in ct.ntk_compartment_ids.items():
                    if val == drg_comp_id:
                        if ("::" in key):
                            drg_comp_name = key
                            continue
                        else:
                            drg_comp_name = key
                            break

                tf_name = commonTools.check_tf_variable(drg_display_name)
                if (drg_id not in drg_ocid):
                    importCommands[reg].write(
                        "\nterraform import \"module.drgs[\\\"" + tf_name + "\\\"].oci_core_drg.drg\" " + drg_info.id)
                    drg_ocid.append(drg_id)

                # Get Attachment Details
                # DRG v2
                if (drg_attachment_info.network_details is not None):
                    attach_type = drg_attachment_info.network_details.type
                    attach_id = drg_attachment_info.network_details.id
                # DRG v1
                else:
                    drg_version = "DRGv1"
                    attach_type = "VCN"
                    attach_id = drg_attachment_info.vcn_id

                oci_obj_names[reg].write("\nDRG Version::::" + drg_version + "::::None::::None")

                vcn_info = None
                if (attach_type.upper() == "VCN"):
                    vcn_drgattach_route_table_id = drg_attachment_info.route_table_id
                    vcn_info = vnc.get_vcn(attach_id).data
                    if (vcn_drgattach_route_table_id is not None):
                        oci_obj_names[reg].write(
                            "\ndrginfo::::" + vcn_info.display_name + "::::" + drg_info.display_name + "::::" + vnc.get_route_table(
                                vcn_drgattach_route_table_id).data.display_name)
                    else:
                        oci_obj_names[reg].write(
                            "\ndrginfo::::" + vcn_info.display_name + "::::" + drg_info.display_name + "::::None")

                    # tf_name = vcn_info.display_name + "_" + drg_attachment_name
                    tf_name = commonTools.check_tf_variable(drg_attachment_name)

                    importCommands[reg].write(
                        "\nterraform import \"module.drg-attachments[\\\"" + tf_name + "\\\"].oci_core_drg_attachment.drg_attachment\" " + drg_attachment_info.id)
                    oci_obj_names[reg].write(
                        "\ndrgattachinfo::::" + vcn_info.display_name + "::::" + drg_display_name + "::::" + drg_attachment_name)

                    drg_route_table_id = drg_attachment_info.drg_route_table_id

                    ##DRG v2
                    drg_route_table_info = None
                    import_drg_route_distribution_info = None
                    drg_route_distribution_statements = None

                    if (drg_route_table_id is not None):
                        drg_rt_ocid.append(drg_route_table_id)
                        drg_route_table_info = vnc.get_drg_route_table(drg_route_table_id).data

                        import_drg_route_distribution_id = drg_route_table_info.import_drg_route_distribution_id
                        if (import_drg_route_distribution_id != None):
                            import_drg_route_distribution_info = vnc.get_drg_route_distribution(
                                import_drg_route_distribution_id).data
                            drg_route_distribution_statements = vnc.list_drg_route_distribution_statements(
                                import_drg_route_distribution_info.id)

                            tf_name = commonTools.check_tf_variable(
                                drg_display_name + "_" + import_drg_route_distribution_info.display_name)
                            if (import_drg_route_distribution_info.display_name not in commonTools.drg_auto_RDs):
                                importCommands[reg].write(
                                    "\nterraform import \"module.drg-route-distributions[\\\"" + tf_name + "\\\"].oci_core_drg_route_distribution.drg_route_distribution\" " + import_drg_route_distribution_info.id)

                                k = 1
                                for stmt in drg_route_distribution_statements.data:
                                    importCommands[reg].write(
                                        "\nterraform import \"module.drg-route-distribution-statements[\\\"" + tf_name + "_statement" + str(
                                            k) + "\\\"].oci_core_drg_route_distribution_statement.drg_route_distribution_statement\" drgRouteDistributions/" + import_drg_route_distribution_info.id + "/statements/" + stmt.id)
                                    k = k + 1

                    print_drgv2(values_for_column_drgv2, region, drg_comp_name, vcn_info, drg_info, drg_attachment_info,
                                drg_route_table_info, import_drg_route_distribution_info,
                                drg_route_distribution_statements)

                # RPC
                elif attach_type.upper() == "REMOTE_PEERING_CONNECTION" and rpc_execution:
                    # Fetch RPC Details
                    drg_route_table_id = drg_attachment_info.drg_route_table_id

                    if (drg_route_table_id is not None):
                        drg_rt_ocid.append(drg_route_table_id)
                        drg_route_table_info = vnc.get_drg_route_table(drg_route_table_id).data

                        import_drg_route_distribution_id = drg_route_table_info.import_drg_route_distribution_id
                        if (import_drg_route_distribution_id != None):
                            import_drg_route_distribution_info = vnc.get_drg_route_distribution(
                                import_drg_route_distribution_id).data
                            drg_route_distribution_statements = vnc.list_drg_route_distribution_statements(
                                import_drg_route_distribution_info.id)

                            tf_name = commonTools.check_tf_variable(
                                drg_display_name + "_" + import_drg_route_distribution_info.display_name)
                            if (import_drg_route_distribution_info.display_name not in commonTools.drg_auto_RDs):
                                importCommands[reg].write(
                                    "\nterraform import \"module.drg-route-distributions[\\\"" + tf_name + "\\\"].oci_core_drg_route_distribution.drg_route_distribution\" " + import_drg_route_distribution_info.id)

                                k = 1
                                for stmt in drg_route_distribution_statements.data:
                                    importCommands[reg].write(
                                        "\nterraform import \"module.drg-route-distribution-statements[\\\"" + tf_name + "_statement" + str(
                                            k) + "\\\"].oci_core_drg_route_distribution_statement.drg_route_distribution_statement\" drgRouteDistributions/" + import_drg_route_distribution_info.id + "/statements/" + stmt.id)
                                    k = k + 1

                    dest_rpc_dict = {}
                    subs_region_list = ct.all_regions[:]
                    if current_region in subs_region_list:

                        subs_region_list.remove(current_region)
                        for new_reg in subs_region_list:
                            config.__setitem__("region", ct.region_dict[new_reg])
                            dest_rpc_dict[new_reg] = oci.core.VirtualNetworkClient(config,
                                                                                   retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
                    SOURCE_RPC_LIST = oci.pagination.list_call_get_all_results(
                        vnc.list_remote_peering_connections,
                        compartment_id=ct.ntk_compartment_ids[
                            ntk_compartment_name])

                    get_rpc_resources(region, SOURCE_RPC_LIST, dest_rpc_dict, vnc,
                                       ct, values_for_column_drgv2, ntk_compartment_name, outdir)
                    rpc_execution = False

            # Get All Other RTs for this DRG only if it is DRGv2
            # DRG v2
            for drg_id in drg_ocid:
                drg_attachment_info = None
                vcn_info = None
                drg_info = vnc.get_drg(drg_id).data

                if drg_info.default_drg_route_tables is not None:
                    DRG_RTs = oci.pagination.list_call_get_all_results(vnc.list_drg_route_tables,
                                                                       drg_id=drg_id)
                    for drg_route_table_info in DRG_RTs.data:
                        drg_rt_id = drg_route_table_info.id
                        # RT associated with attachment already processed above
                        if (drg_rt_id in drg_rt_ocid):
                            continue
                        # Process other RTs of this DRG
                        drg_rt_ocid.append(drg_rt_id)
                        import_drg_route_distribution_info = None
                        drg_route_distribution_statements = None

                        import_drg_route_distribution_id = drg_route_table_info.import_drg_route_distribution_id
                        if (import_drg_route_distribution_id != None):
                            import_drg_route_distribution_info = vnc.get_drg_route_distribution(
                                import_drg_route_distribution_id).data
                            drg_route_distribution_statements = vnc.list_drg_route_distribution_statements(
                                import_drg_route_distribution_info.id)

                            tf_name = commonTools.check_tf_variable(
                                drg_display_name + "_" + import_drg_route_distribution_info.display_name)
                            if (import_drg_route_distribution_info.display_name not in commonTools.drg_auto_RDs):
                                importCommands[reg].write(
                                    "\nterraform import \"module.drg-route-distributions[\\\"" + tf_name + "\\\"].oci_core_drg_route_distribution.drg_route_distribution\" " + import_drg_route_distribution_info.id)

                                k = 1
                                for stmt in drg_route_distribution_statements.data:
                                    importCommands[reg].write(
                                        "\nterraform import \"module.drg-route-distribution-statements[\\\"" + tf_name + "_statement" + str(
                                            k) + "\\\"].oci_core_drg_route_distribution_statement.drg_route_distribution_statement\" drgRouteDistributions/" + import_drg_route_distribution_info.id + "/statements/" + stmt.id)
                                    k = k + 1
                        print_drgv2(values_for_column_drgv2, region, drg_comp_name, vcn_info, drg_info,
                                    drg_attachment_info, drg_route_table_info,
                                    import_drg_route_distribution_info,
                                    drg_route_distribution_statements)

    commonTools.write_to_cd3(values_for_column_drgv2, cd3file, "DRGs")
    print("RPCs exported to CD3\n")
    print("DRGs exported to CD3\n")

    # Fetch VCNs
    for reg in export_regions:
        importCommands[reg].write("\n######### Writing import for VCNs #########\n")
        config.__setitem__("region", ct.region_dict[reg])
        vnc = VirtualNetworkClient(config=config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,signer=signer)
        region = reg.capitalize()
        comp_ocid_done = []
        for ntk_compartment_name in export_compartments:
            # if ct.ntk_compartment_ids[ntk_compartment_name] not in comp_ocid_done:
            # if (input_compartment_names is not None and ntk_compartment_name not in input_compartment_names):
            #    continue
            # comp_ocid_done.append(ct.ntk_compartment_ids[ntk_compartment_name])
            vcns = oci.pagination.list_call_get_all_results(vnc.list_vcns,
                                                            compartment_id=ct.ntk_compartment_ids[ntk_compartment_name],
                                                            lifecycle_state="AVAILABLE")
            for vcn in vcns.data:
                vcn_info = vcn
                # Fetch VCN components assuming components are in same comp as VCN

                # DRG attachment is in same compartment as VCN by default
                DRG_Attachments = oci.pagination.list_call_get_all_results(vnc.list_drg_attachments,
                                                                           compartment_id=ct.ntk_compartment_ids[
                                                                               ntk_compartment_name], vcn_id=vcn.id)
                drg_info = None
                igw_info = None
                ngw_info = None
                sgw_info = None

                for drg_attachment_info in DRG_Attachments.data:
                    drg_id = drg_attachment_info.drg_id
                    drg_info = vnc.get_drg(drg_id).data

                # igw_display_name = "n"
                IGWs = oci.pagination.list_call_get_all_results(vnc.list_internet_gateways,
                                                                compartment_id=ct.ntk_compartment_ids[
                                                                    ntk_compartment_name],
                                                                vcn_id=vcn.id, lifecycle_state="AVAILABLE")
                for igw in IGWs.data:
                    igw_info = igw
                    igw_display_name = igw_info.display_name
                    tf_name = vcn_info.display_name + "_" + igw_display_name
                    tf_name = commonTools.check_tf_variable(tf_name)
                    importCommands[reg].write(
                        "\nterraform import \"module.igws[\\\"" + tf_name + "\\\"].oci_core_internet_gateway.internet_gateway\" " + igw_info.id)

                # ngw_display_name = "n"
                NGWs = oci.pagination.list_call_get_all_results(vnc.list_nat_gateways,
                                                                compartment_id=ct.ntk_compartment_ids[
                                                                    ntk_compartment_name],
                                                                vcn_id=vcn.id, lifecycle_state="AVAILABLE")
                for ngw in NGWs.data:
                    ngw_info = ngw
                    ngw_display_name = ngw_info.display_name
                    tf_name = vcn_info.display_name + "_" + ngw_display_name
                    tf_name = commonTools.check_tf_variable(tf_name)

                    importCommands[reg].write(
                        "\nterraform import \"module.ngws[\\\"" + tf_name + "\\\"].oci_core_nat_gateway.nat_gateway\" " + ngw_info.id)

                # sgw_display_name = "n"
                SGWs = oci.pagination.list_call_get_all_results(vnc.list_service_gateways,
                                                                compartment_id=ct.ntk_compartment_ids[
                                                                    ntk_compartment_name],
                                                                vcn_id=vcn.id, lifecycle_state="AVAILABLE")
                for sgw in SGWs.data:
                    sgw_info = sgw
                    sgw_display_name = sgw_info.display_name
                    tf_name = vcn_info.display_name + "_" + sgw_display_name
                    tf_name = commonTools.check_tf_variable(tf_name)
                    importCommands[reg].write(
                        "\nterraform import \"module.sgws[\\\"" + tf_name + "\\\"].oci_core_service_gateway.service_gateway\" " + sgw_info.id)

                lpg_display_names = ""
                LPGs = oci.pagination.list_call_get_all_results(vnc.list_local_peering_gateways,
                                                                compartment_id=ct.ntk_compartment_ids[
                                                                    ntk_compartment_name],
                                                                vcn_id=vcn.id)
                for lpg in LPGs.data:
                    if (lpg.lifecycle_state != "AVAILABLE"):
                        continue
                    lpg_info = lpg
                    lpg_display_names = lpg_info.display_name + "," + lpg_display_names

                    lpg_route_table_id = lpg_info.route_table_id
                    if (lpg_route_table_id is not None):
                        oci_obj_names[region.lower()].write(
                            "\nlpginfo::::" + vcn_info.display_name + "::::" + lpg_info.display_name + "::::" + vnc.get_route_table(
                                lpg_route_table_id).data.display_name)

                    tf_name = vcn_info.display_name + "_" + lpg_info.display_name
                    tf_name = commonTools.check_tf_variable(tf_name)
                    importCommands[reg].write(
                        "\nterraform import \"module.exported-lpgs[\\\"" + tf_name + "\\\"].oci_core_local_peering_gateway.local_peering_gateway\" " + lpg_info.id)

                if (lpg_display_names == ""):
                    lpg_display_names = "n"
                elif (lpg_display_names[-1] == ','):
                    lpg_display_names = lpg_display_names[:-1]

                # Fill VCNs Tab
                print_vcns(values_for_column_vcns, region, ntk_compartment_name, vcn_info, drg_info, igw_info, ngw_info,
                           sgw_info, lpg_display_names)

    commonTools.write_to_cd3(values_for_column_vcns, cd3file, "VCNs")
    print("VCNs exported to CD3\n")

    for reg in export_regions:
        importCommands[reg].close()
        oci_obj_names[reg].close()


def export_dhcp(inputfile, outdir, service_dir, config, signer, ct, export_compartments=[], export_regions=[]):
    global sheet_dict_dhcp

    cd3file = inputfile
    if ('.xls' not in cd3file):
        print("\nAcceptable cd3 format: .xlsx")
        exit()

    # Read CD3
    df, values_for_column_dhcp = commonTools.read_cd3(cd3file, "DHCP")

    # Get dict for columns from Excel_Columns
    sheet_dict_dhcp = ct.sheet_dict["DHCP"]

    print("Fetching DHCP...")

    # Create backups
    for reg in export_regions:
        if (os.path.exists(outdir + "/" + reg + "/" + service_dir + "/tf_import_commands_network_dhcp_nonGF.sh")):
            commonTools.backup_file(outdir + "/" + reg + "/" + service_dir, "tf_import_network",
                                    "tf_import_commands_network_dhcp_nonGF.sh")
        importCommands[reg] = open(outdir + "/" + reg + "/" + service_dir + "/tf_import_commands_network_dhcp_nonGF.sh",
                                   "w")
        importCommands[reg].write("#!/bin/bash")
        importCommands[reg].write("\n")
        importCommands[reg].write("terraform init")

    print("Tab- DHCP would be overwritten during export process!!!")
    for reg in export_regions:
        importCommands[reg].write("\n\n######### Writing import for DHCP #########\n\n")
        config.__setitem__("region", ct.region_dict[reg])
        vnc = VirtualNetworkClient(config=config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,signer=signer)
        region = reg.capitalize()
        # comp_ocid_done = []
        for ntk_compartment_name in export_compartments:
            vcns = oci.pagination.list_call_get_all_results(vnc.list_vcns,
                                                            compartment_id=ct.ntk_compartment_ids[ntk_compartment_name],
                                                            lifecycle_state="AVAILABLE")
            for vcn in vcns.data:
                vcn_info = vnc.get_vcn(vcn.id).data
                #            comp_ocid_done_again = []
                for ntk_compartment_name_again in export_compartments:
                    DHCPs = oci.pagination.list_call_get_all_results(vnc.list_dhcp_options,
                                                                     compartment_id=ct.ntk_compartment_ids[
                                                                         ntk_compartment_name_again], vcn_id=vcn.id,
                                                                     lifecycle_state="AVAILABLE")
                    for dhcp in DHCPs.data:
                        dhcp_info = dhcp
                        print_dhcp(values_for_column_dhcp, region, ntk_compartment_name_again, vcn_info.display_name,
                                   dhcp_info)
    commonTools.write_to_cd3(values_for_column_dhcp, cd3file, "DHCP")
    print("DHCP exported to CD3\n")
    for reg in export_regions:
        importCommands[reg].close()


def export_subnets_vlans(inputfile, outdir, service_dir, config, signer, ct, export_compartments=[], export_regions=[]):
    global sheet_dict_subnets_vlans

    cd3file = inputfile
    if ('.xls' not in cd3file):
        print("\nAcceptable cd3 format: .xlsx")
        exit()

    # Read CD3
    df, values_for_column_subnets_vlans = commonTools.read_cd3(cd3file, "SubnetsVLANs")

    # Get dict for columns from Excel_Columns
    sheet_dict_subnets_vlans = ct.sheet_dict["SubnetsVLANs"]

    print("Fetching Subnets VLANs...")
    if len(service_dir) != 0:
        service_dir_network = service_dir['network']
        service_dir_vlan = service_dir['vlan']
    else:
        service_dir_network = ""
        service_dir_vlan = ""

    # Create backups for subnets/vlans tf import shell script files
    for reg in export_regions:
        if (os.path.exists(
                outdir + "/" + reg + "/" + service_dir_network + "/tf_import_commands_network_subnets_nonGF.sh")):
            commonTools.backup_file(outdir + "/" + reg + "/" + service_dir_network, "tf_import_network",
                                    "tf_import_commands_network_subnets_nonGF.sh")
        importCommands[reg] = open(
            outdir + "/" + reg + "/" + service_dir_network + "/tf_import_commands_network_subnets_nonGF.sh", "w")
        importCommands[reg].write("#!/bin/bash")
        importCommands[reg].write("\n")
        importCommands[reg].write("terraform init")

        if (os.path.exists(outdir + "/" + reg + "/" + service_dir_vlan + "/tf_import_commands_network_vlans_nonGF.sh")):
            commonTools.backup_file(outdir + "/" + reg + "/" + service_dir_vlan, "tf_import_network",
                                    "tf_import_commands_network_vlans_nonGF.sh")
        importCommands_vlan[reg] = open(
            outdir + "/" + reg + "/" + service_dir_vlan + "/tf_import_commands_network_vlans_nonGF.sh", "w")
        importCommands_vlan[reg].write("#!/bin/bash")
        importCommands_vlan[reg].write("\n")
        importCommands[reg].write("terraform init")

    print("Tab- 'SubnetsVLANs' would be overwritten during export process!!!")
    for reg in export_regions:
        importCommands[reg].write("\n\n######### Writing import for Subnets #########\n\n")
        importCommands_vlan[reg].write("\n\n######### Writing import for VLANs #########\n\n")
        config.__setitem__("region", ct.region_dict[reg])
        vnc = VirtualNetworkClient(config=config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,signer=signer)
        region = reg.capitalize()

        skip_vlans = 0
        try:
            VLANs = oci.pagination.list_call_get_all_results(vnc.list_vlans,
                                                             compartment_id=ct.ntk_compartment_ids['root'])
        except Exception as e:
            if ('Tenancy is NOT whitelisted for VMware SKU' in str(e)):
                print('Tenancy is NOT whitelisted for VMware SKU..skipping export of VLANs')
                skip_vlans = 1

        for ntk_compartment_name in export_compartments:
            vcns = oci.pagination.list_call_get_all_results(vnc.list_vcns,
                                                            compartment_id=ct.ntk_compartment_ids[ntk_compartment_name],
                                                            lifecycle_state="AVAILABLE")
            for vcn in vcns.data:
                vcn_info = vnc.get_vcn(vcn.id).data
                for ntk_compartment_name_again in export_compartments:

                    # Subnet Data
                    subnet_vlan_in_excel = "Subnet"
                    Subnets = oci.pagination.list_call_get_all_results(vnc.list_subnets,
                                                                       compartment_id=ct.ntk_compartment_ids[
                                                                           ntk_compartment_name_again], vcn_id=vcn.id,
                                                                       lifecycle_state="AVAILABLE")
                    for subnet in Subnets.data:
                        subnet_info = subnet
                        dhcp_id = subnet_info.dhcp_options_id
                        dhcp_name = vnc.get_dhcp_options(dhcp_id).data.display_name
                        if ("Default DHCP Options for " in dhcp_name):
                            dhcp_name = ""

                        rt_id = subnet_info.route_table_id
                        rt_name = vnc.get_route_table(rt_id).data.display_name
                        if ("Default Route Table for " in rt_name):
                            rt_name = "n"

                        sl_ids = subnet_info.security_list_ids
                        sl_names = ""
                        add_def_seclist = 'n'
                        for sl_id in sl_ids:
                            sl_name = vnc.get_security_list(sl_id).data.display_name
                            if ("Default Security List for " in sl_name):
                                add_def_seclist = 'y'
                                continue
                            sl_names = sl_name + "," + sl_names
                        if (sl_names == ""):
                            sl_names = "n"
                        elif (sl_names != "" and sl_names[-1] == ','):
                            sl_names = sl_names[:-1]
                        # Fill Subnets tab
                        print_subnets_vlans(values_for_column_subnets_vlans, region, ntk_compartment_name_again,
                                            vcn_info.display_name, subnet_info, dhcp_name,
                                            rt_name, sl_names, add_def_seclist, subnet_vlan_in_excel)

                    # VLAN Data
                    if skip_vlans == 1:
                        continue

                    subnet_vlan_in_excel = "VLAN"
                    VLANs = oci.pagination.list_call_get_all_results(vnc.list_vlans,
                                                                     compartment_id=ct.ntk_compartment_ids[
                                                                         ntk_compartment_name_again], vcn_id=vcn.id,
                                                                     lifecycle_state="AVAILABLE")
                    for vlan in VLANs.data:
                        vlan_info = vlan
                        dhcp_name = ""

                        rt_id = vlan_info.route_table_id
                        rt_name = vnc.get_route_table(rt_id).data.display_name
                        if ("Default Route Table for " in rt_name):
                            rt_name = "n"

                        nsg_ids = vlan_info.nsg_ids
                        nsg_names = ""
                        for nsg_id in nsg_ids:
                            nsg_name = vnc.get_network_security_group(nsg_id).data.display_name
                            nsg_names = nsg_name + "," + nsg_names
                        if (nsg_names != "" and nsg_names[-1] == ','):
                            nsg_names = nsg_names[:-1]

                        add_def_seclist = 'n'

                        # Fill Subnets tab
                        print_subnets_vlans(values_for_column_subnets_vlans, region, ntk_compartment_name_again,
                                            vcn_info.display_name, vlan_info, dhcp_name,
                                            rt_name, nsg_names, add_def_seclist, subnet_vlan_in_excel)

    commonTools.write_to_cd3(values_for_column_subnets_vlans, cd3file, "SubnetsVLANs")
    print("SubnetsVLANs exported to CD3\n")

    for reg in export_regions:
        importCommands[reg].write('\n\nterraform plan\n')
        importCommands[reg].close()
        importCommands_vlan[reg].write('\n\nterraform plan\n')
        importCommands_vlan[reg].close()

# Execution of the code begins here
def export_networking(inputfile, outdir, service_dir, config, signer, ct, export_compartments=[], export_regions=[]):

    print("\nCD3 excel file should not be opened during export process!!!\n")

    if len(service_dir) != 0:
        service_dir_network = service_dir['network']
        service_dir_nsg = service_dir['nsg']
    else:
        service_dir_network = ""
        service_dir_nsg = ""

    # Fetch Major Objects
    export_major_objects(inputfile, outdir, service_dir_network, config=config, signer=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions)

    # Fetch DHCP
    export_dhcp(inputfile, outdir, service_dir_network, config=config, signer=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions)

    # Fetch Subnets and VLANs
    export_subnets_vlans(inputfile, outdir, service_dir, config=config, signer=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions)

    # Fetch RouteRules and SecRules
    export_seclist(inputfile, outdir, service_dir_network, config=config, signer=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions,_tf_import_cmd=True)

    export_routetable(inputfile, outdir, service_dir_network, config1=config, signer1=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions, _tf_import_cmd=True)

    export_drg_routetable(inputfile, outdir, service_dir_network, config1=config, signer1=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions, _tf_import_cmd=True)

    # Fetch NSGs
    export_nsg(inputfile, outdir, service_dir_nsg, config=config, signer=signer, ct=ct, export_compartments=export_compartments, export_regions=export_regions, _tf_import_cmd=True)