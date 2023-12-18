import com.cloudbees.hudson.plugins.folder.*
//import org.jenkinsci.plugins.workflow.job.WorkflowJob
import jenkins.model.Jenkins

Jenkins jenkins = Jenkins.instance
def JENKINS_HOME = System.getenv("JENKINS_HOME")

File file = new File("$JENKINS_HOME/jenkins.properties")
file.withReader { reader ->
     while ((line = reader.readLine()) != null) {
          if (line.startsWith('git_url')) {
            git_url = Eval.me(line.split("=")[1])
        }
          if (line.startsWith('regions')) {
            regions = Eval.me(line.split("=")[1])
        }
          if (line.startsWith('outdir_structure')) {
            outdir_structure = Eval.me(line.split("=")[1])
        }
          if (line.startsWith('services')) {
            services = Eval.me(line.split("=")[1])
        }
      }
    }
def tfApplyJobName = "Terraform-Plan-OPA-Apply"
def tfDestroyJobName = "Terraform-Destroy"

for (os in outdir_structure) {
        def ost = jenkins.getItem("terraform_files")
        if (ost == null) {
                ost = jenkins.createProject(Folder.class,"terraform_files")
               }
        for (reg in regions) {
                def folder = ost.getItem(reg)
                if (folder == null) {
                        folder = ost.createProject(Folder.class, reg)
                        if (os == "Single_Outdir"){
                                def tfApplyXml =
"""\
<flow-definition>
        <actions/>
        <description/>
        <keepDependencies>false</keepDependencies>
        <properties>
                <hudson.model.ParametersDefinitionProperty>
                        <parameterDefinitions>
                                <hudson.model.StringParameterDefinition>
                                        <name>Region</name>
                                        <defaultValue>${reg}</defaultValue>
                                        <description>Tenancy region where resource are to be deployed. Required for both single and multiple out directory structure</description>
                                </hudson.model.StringParameterDefinition>
                        </parameterDefinitions>
                </hudson.model.ParametersDefinitionProperty>
        </properties>
        <triggers/>
        <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
                <scriptPath>singleOutput.groovy</scriptPath>
                <lightweight>false</lightweight>
                <scm class="hudson.plugins.git.GitSCM">
                        <userRemoteConfigs>
                                <hudson.plugins.git.UserRemoteConfig>
                                        <url>${git_url}</url>
                                </hudson.plugins.git.UserRemoteConfig>
                        </userRemoteConfigs>
                        <branches>
                                <hudson.plugins.git.BranchSpec>
                                        <name>main</name>
                                </hudson.plugins.git.BranchSpec>
                        </branches>
                        <configVersion>2</configVersion>
                        <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
                        <gitTool>Default</gitTool>
                </scm>
        </definition>
</flow-definition>
"""

                        def tfDestroyXml =
"""\
<flow-definition>
        <actions/>
        <description/>
        <keepDependencies>false</keepDependencies>
        <properties>
                <hudson.model.ParametersDefinitionProperty>
                        <parameterDefinitions>
                                <hudson.model.StringParameterDefinition>
                                        <name>Region</name>
                                        <defaultValue>${reg}</defaultValue>
                                        <description>Tenancy region where resource are to be deployed. Required for both single and multiple out directory structure</description>
                                </hudson.model.StringParameterDefinition>
                        </parameterDefinitions>
                </hudson.model.ParametersDefinitionProperty>
        </properties>
        <triggers/>
        <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
                <scriptPath>singleOutput-tf-destroy.groovy</scriptPath>
                <lightweight>false</lightweight>
                <scm class="hudson.plugins.git.GitSCM">
                        <userRemoteConfigs>
                                <hudson.plugins.git.UserRemoteConfig>
                                        <url>${git_url}</url>
                                </hudson.plugins.git.UserRemoteConfig>
                        </userRemoteConfigs>
                        <branches>
                                <hudson.plugins.git.BranchSpec>
                                        <name>main</name>
                                </hudson.plugins.git.BranchSpec>
                        </branches>
                        <configVersion>2</configVersion>
                        <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
                        <gitTool>Default</gitTool>
                </scm>
        </definition>
</flow-definition>
"""

                                def tfApplyxmlStream = new ByteArrayInputStream(tfApplyXml.getBytes())
                                job1 = folder.createProjectFromXML(tfApplyJobName, tfApplyxmlStream)
                                                                def tfDestroyxmlStream = new ByteArrayInputStream(tfDestroyXml.getBytes())
                                job2 = folder.createProjectFromXML(tfDestroyJobName, tfDestroyxmlStream)

                        }
                        if (os == "Multiple_Outdir"){
                                for (svc in services) {
                                        def svobjt = folder.getItem(svc)
                                        if (svobjt == null) {
                                                svobjt = folder.createProject(Folder.class, svc)
                                                 def tfApplyXml =
"""\
<flow-definition>
        <actions/>
        <description/>
        <keepDependencies>false</keepDependencies>
        <properties>
                <com.sonyericsson.rebuild.RebuildSettings plugin="rebuild@320.v5a_0933a_e7d61">
                        <autoRebuild>true</autoRebuild>
                        <rebuildDisabled>false</rebuildDisabled>
                </com.sonyericsson.rebuild.RebuildSettings>
                <hudson.model.ParametersDefinitionProperty>
                        <parameterDefinitions>
                                <hudson.model.StringParameterDefinition>
                                        <name>Region</name>
                                        <defaultValue>${reg}</defaultValue>
                                        <description>Tenancy region where resource are to be deployed. Required for both single and multiple out directory structure</description>
                                </hudson.model.StringParameterDefinition>
                                <hudson.model.StringParameterDefinition>
                                        <name>Service</name>
                                        <defaultValue>${svc}</defaultValue>
                                        <description>Service to be deployed incase of multiple outdirectory structure</description>
                                </hudson.model.StringParameterDefinition>
                        </parameterDefinitions>
                </hudson.model.ParametersDefinitionProperty>
        </properties>
        <triggers/>
        <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
                <scriptPath>multiOutput.groovy</scriptPath>
                <lightweight>false</lightweight>
                <scm class="hudson.plugins.git.GitSCM">
                        <userRemoteConfigs>
                                <hudson.plugins.git.UserRemoteConfig>
                                        <url>${git_url}</url>
                                </hudson.plugins.git.UserRemoteConfig>
                        </userRemoteConfigs>
                        <branches>
                                <hudson.plugins.git.BranchSpec>
                                        <name>main</name>
                                </hudson.plugins.git.BranchSpec>
                        </branches>
                        <configVersion>2</configVersion>
                        <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
                        <gitTool>Default</gitTool>
                </scm>
        </definition>
</flow-definition>
"""

                                def tfDestroyXml =
"""\
<flow-definition>
        <actions/>
        <description/>
        <keepDependencies>false</keepDependencies>
        <properties>
                <com.sonyericsson.rebuild.RebuildSettings plugin="rebuild@320.v5a_0933a_e7d61">
                        <autoRebuild>true</autoRebuild>
                        <rebuildDisabled>false</rebuildDisabled>
                </com.sonyericsson.rebuild.RebuildSettings>
                <hudson.model.ParametersDefinitionProperty>
                        <parameterDefinitions>
                                <hudson.model.StringParameterDefinition>
                                        <name>Region</name>
                                        <defaultValue>${reg}</defaultValue>
                                        <description>Tenancy region where resource are to be deployed. Required for both single and multiple out directory structure</description>
                                </hudson.model.StringParameterDefinition>
                                <hudson.model.StringParameterDefinition>
                                        <name>Service</name>
                                        <defaultValue>${svc}</defaultValue>
                                        <description>Service to be deployed incase of multiple outdirectory structure</description>
                                </hudson.model.StringParameterDefinition>
                        </parameterDefinitions>
                </hudson.model.ParametersDefinitionProperty>
        </properties>
        <triggers/>
        <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
                <scriptPath>multiOutput-tf-destroy.groovy</scriptPath>
                <lightweight>false</lightweight>
                <scm class="hudson.plugins.git.GitSCM">
                        <userRemoteConfigs>
                                <hudson.plugins.git.UserRemoteConfig>
                                        <url>${git_url}</url>
                                </hudson.plugins.git.UserRemoteConfig>
                        </userRemoteConfigs>
                        <branches>
                                <hudson.plugins.git.BranchSpec>
                                        <name>main</name>
                                </hudson.plugins.git.BranchSpec>
                        </branches>
                        <configVersion>2</configVersion>
                        <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
                        <gitTool>Default</gitTool>
                </scm>
        </definition>
</flow-definition>
"""
                                                def tfApplyxmlStream = new ByteArrayInputStream(tfApplyXml.getBytes())
                                                job1 = svobjt.createProjectFromXML(tfApplyJobName, tfApplyxmlStream)
                                                def tfDestroyxmlStream = new ByteArrayInputStream(tfDestroyXml.getBytes())
                                                job2 = svobjt.createProjectFromXML(tfDestroyJobName, tfDestroyxmlStream)
                                        }
                                }
                        }
                }
        }
}
