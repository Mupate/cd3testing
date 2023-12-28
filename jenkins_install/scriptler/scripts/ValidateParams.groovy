valid_params = ""
def gf_options_map = [
"Validate CD3":["Validate Compartments","Validate Groups","Validate Policies","Validate Tags","Validate Networks","Validate DNS","Validate Instances","Validate Block Volumes","Validate FSS","Validate Buckets"],
"Identity":["Add/Modify/Delete Compartments", "Add/Modify/Delete Groups","Add/Modify/Delete Policies", "Add/Modify/Delete Users", "Add/Modify/Delete Network Sources"],
"Network":["Create Network", "Modify Network","Security Rules", "Route Rules", "DRG Route Rules", "Network Security Groups", "Add/Modify/Delete VLANs", "Customer Connectivity"],
"DNS Management":["Add/Modify/Delete DNS Views/Zones/Records", "Add/Modify/Delete DNS Resolvers"],
"Compute":["Add/Modify/Delete Dedicated VM Hosts", "Add/Modify/Delete Instances/Boot Backup Policy"],
"Storage":["Add/Modify/Delete Block Volumes/Block Backup Policy", "Add/Modify/Delete File Systems", "Add/Modify/Delete Object Storage Buckets"],
"Database":["Add/Modify/Delete Virtual Machine or Bare Metal DB Systems", "Add/Modify/Delete EXA Infra and EXA VM Clusters", "Add/Modify/Delete ADBs"],
"Load Balancers":["Add/Modify/Delete Load Balancers", "Add/Modify/Delete Network Load Balancers"],
"Management Services":["Add/Modify/Delete Notifications", "Add/Modify/Delete Events", "Add/Modify/Delete Alarms", "Add/Modify/Delete ServiceConnectors"],
"Developer Services":["Upload current terraform files/state to Resource Manager", "Add/Modify/Delete OKE Cluster and Nodepools"],
"Logging Services":["Enable VCN Flow Logs", "Enable LBaaS Logs", "Enable Object Storage Buckets Write Logs"],
"CIS Compliance Features":["CIS Compliance Checking Script", "Create Key/Vault", "Create Default Budget", "Enable Cloud Guard"],
"CD3 Services":["Fetch Compartments OCIDs to variables file", "Fetch Protocols to OCI_Protocols"]
]
def non_gf_options_map = [
"Export Identity":["Export Compartments/Groups/Policies", "Export Users", "Export Network Sources"],
"Export Network":["Export all Network Components", "Export Network components for VCNs/DRGs/DRGRouteRulesinOCI Tabs", "Export Network components for DHCP Tab", "Export Network components for SecRulesinOCI Tab", "Export Network components for RouteRulesinOCI Tab", "Export Network components for SubnetsVLANs Tab", "Export Network components for NSGs Tab"],
"Export DNS Management":["Export DNS Views/Zones/Records", "Export DNS Resolvers"],
"Export Compute":["Export Dedicated VM Hosts", "Export Instances (excludes instances launched by OKE)"],
"Export Storage":["Export Block Volumes/Block Backup Policy", "Export File Systems", "Export Object Storage Buckets"],
"Export Databases":["Export Virtual Machine or Bare Metal DB Systems", "Export EXA Infra and EXA VMClusters", "Export ADBs"],
"Export Load Balancers":["Export Load Balancers", "Export Network Load Balancers"],
"Export Management Services":["Export Notifications", "Export Events", "Export Alarms", "Export Service Connectors"],
"Export Developer Services":["Export OKE cluster and Nodepools"],
"CD3 Services":["Fetch Compartments OCIDs to variables file", "Fetch Protocols to OCI_Protocols"]
]
for (mitem in MainOptions.split(",")) {
	if (mitem.contains("Tag") || mitem.contains("OCVS") ) {
    	if (valid_params == ""){
      		valid_params = "Passed"
    	} 
    	continue
	}
 	for (sitem in SubOptions.split(",")) {
		if (Workflow.equals("Create Resources in OCI (Greenfield Workflow)")){
			if (sitem in gf_options_map[mitem]) {
				valid_params = "Passed"
			}else {
				valid_params = "Failed"
			}		
		}else {
			if (sitem in non_gf_options_map[mitem]) {
				valid_params = "Passed"
			}else {
				valid_params = "Failed"
			}
		}
	}
}
return["${valid_params}:selected:disabled"]