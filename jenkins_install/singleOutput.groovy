/* Set the various stages of the build */
def tf_plan = "Changes"
pipeline {
    agent any
    options {
        ansiColor('xterm')
    }
    stages {
        stage('Terraform Plan') {
            when {
                expression {
                    return env.GIT_BRANCH == 'origin/main';
                }
            }

            steps {
                script {
                    def jobName = env.JOB_NAME
                    def parts = jobName.split('/')

                    // Assuming the job name format is <region_name>/job/job_name
                    def regionName = parts[1]

                    // Set environment variables for reuse in subsequent stages
                    env.Region = regionName
                    dir("${WORKSPACE}/${env.Region}") {
                            sh 'terraform init -upgrade'
                    }

                    // Run Terraform plan and capture the output
                    def terraformPlanOutput = sh(script: "cd \"${WORKSPACE}/${env.Region}\" && terraform plan -out=tfplan.out", returnStdout: true).trim()

                    // Check if the plan contains any changes
                    if (terraformPlanOutput.contains('No changes.')) {
                        echo 'No changes in Terraform plan. Skipping further stages.'
                        tf_plan = "No Changes"
                    } else {
                        // If there are changes, proceed with applying the plan
                        echo "Changes detected in Terraform plan. Proceeding with apply. \n${terraformPlanOutput}"

                    }
                }
            }
        }
        /** OPA Stage **/
        stage('OPA') {
            when {
                allOf{
                    expression { return env.GIT_BRANCH == 'origin/main'}
                    expression { return tf_plan == "Changes" }
                }
            }

            steps {
                script {
                    // Run Terraform show and capture the output
                    sh "set +x && cd \"${WORKSPACE}/${env.Region}\" && terraform show -json tfplan.out > tfplan.json"
                    // Run OPA eval
                    def opaOutput = sh(script: "opa eval -f pretty -b /cd3user/oci_tools/cd3_automation_toolkit/user-scripts/OPA/ -i \"${WORKSPACE}/${env.Region}/tfplan.json\" data.terraform.deny",returnStdout: true).trim()

                    if (opaOutput == '[]') {
                        echo "No OPA rules are violated. Proceeding with the next stage."
                    }
                    else {
                        echo "OPA Output:\n${opaOutput}"
                        unstable(message:"OPA Rules are violated.")
                    }
                }
            }
        }

       stage('Get Approval') {
            when {
                allOf{
                    expression { return env.GIT_BRANCH == 'origin/main'}
                    expression {return tf_plan == "Changes"}
                }
            }

            options {
                timeout(time: 1440, unit: 'MINUTES')                       // 24hours
            }

            steps {
                script {
                    input message: "Do you want to apply the plan?"
                    echo "Approval for the Apply Granted!"
                }
            }
       }

        stage('Terraform Apply') {
            when {
                allOf{
                    expression { return env.GIT_BRANCH == 'origin/main'}
                    expression {return tf_plan == "Changes"}
                }
            }

            steps {
                script {
                  sh "cd \"${WORKSPACE}/${env.Region}\" && terraform apply --auto-approve tfplan.out"
                }
            }
        }
    }
}
