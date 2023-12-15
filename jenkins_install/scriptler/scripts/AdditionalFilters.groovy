html_to_be_rendered = "<table><tr>"

if(Workflow.equals("Non-Greenfield")){

html_to_be_rendered = """
    ${html_to_be_rendered}
    <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"reg_filter=[\"></td>
    <td><label title=\"service1-label\" class=\" \">Region Filter : </label></td>
    <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>

    </tr>

    <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"comp_filter=[\"></td>
    <td><label title=\"service1-label\" class=\" \">Compartment Filter : </label></td>
    <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
    </tr>

"""
}
for (item in SubOptions.split(",")) {
    if (item.equals("Export Instances (excludes instances launched by OKE)")) {
        html_to_be_rendered = """
        ${html_to_be_rendered}

       <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"ins_pattern_filter=[\"></td>
    <td><label title=\"service1-label\" class=\" \">Compute Instance Pattern Filter :  </label></td>
    <td>
    <input type=\"text\" class=\" \" name=\"value\" > </br>
    </td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td></tr>

     <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"ins_ad_filter=[\"></td>
    <td><label title=\"service1-label\" class=\" \">Compute instance AD filter : </label></td>
    <td>
    <input type=\"text\" class=\" \" name=\"value\" > </br>
    </td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td></tr>


      """
      }

   if (item.equals("Export Block Volumes/Block Backup Policy")) {
      html_to_be_rendered = """
      ${html_to_be_rendered}
       <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"bv_pattern_filter=[\"></td>
    <td><label title=\"service1-label\" class=\" \">Block Volume Pattern filter : </label></td>
    <td>
    <input type=\"text\" class=\" \" name=\"value\" > </br>
    </td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td></tr>
 <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"bv_ad_filter=[\"></td>
    <td><label title=\"service1-label\" class=\" \">Block Volume AD filter : </label></td>
    <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td></tr>
      """
   }

   if (item.equals('Export DNS Views/Zones/Records')){
        html_to_be_rendered = """
        ${html_to_be_rendered}

        <tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"default_dns=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Export Default views/Zones/Records </label></td>
        <td>
       <input name=\"value\"  json=\"service1\" type=\"checkbox\" class=\" \">

       </td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>
         """
   }
 if (item.equals('Upload current terraform files/state to Resource Manager')){
        html_to_be_rendered = """
        ${html_to_be_rendered}


<tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"orm_region=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Enter region (comma separated without spaces if multiple) for which you want to upload Terraform Stack - eg ashburn,phoenix,global : </label></td>
         <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>
         """
   }

 if (item.equals('Create Key/Vault')){
        html_to_be_rendered = """
        ${html_to_be_rendered}


<tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"vault_region=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Enter region name eg ashburn where you want to create Key/Vault : </label></td>
         <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>
<tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"vault_comp=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Enter name of compartment as it appears in OCI Console : </label></td>
         <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>
         """
   }

 if (item.equals('Create Default Budget')){
        html_to_be_rendered = """
        ${html_to_be_rendered}


<tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"budget_amount=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Enter Monthly Budget Amount (in USD) :  </label></td>
         <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>
<tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"budget_threshold=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Enter Threshold Percentage of Budget : </label></td>
         <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>
         """
   }

 if (item.equals('Enable Cloud Guard')){
        html_to_be_rendered = """
        ${html_to_be_rendered}


<tr>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"cg_region=[\"></td>
     <td><label title=\"service1-label\" class=\" \">Enter Reporting Region for Cloud Guard eg london :  </label></td>
         <td><input type=\"text\" class=\" \" name=\"value\" > </br></td>
   <td><input type=\"hidden\" id=\"sep1\" name=\"value\" value=\"]@\"></td>
       </tr>

         """
   }

}

html_to_be_rendered = "${html_to_be_rendered} </tr></table>"

return html_to_be_rendered