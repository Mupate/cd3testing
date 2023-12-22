/* Set the various stages of the build */
pipeline {
    agent any
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
                    echo "Region Name: ${regionName}"


                    // Set environment variables for reuse in subsequent stages
                    env.Region = regionName
                    dir("${WORKSPACE}/${env.Region}") {
                            sh 'terraform init -upgrade'
                    }

                    // Run Terraform plan and capture the output
                    def terraformPlanOutput = sh(script: "cd \"${WORKSPACE}/${env.Region}\" && terraform plan -
out=tfplan.out", returnStdout: true).trim()

                    // Check if the plan contains any changes
                    if (terraformPlanOutput.contains('No changes.')) {
                        echo 'No changes in Terraform plan. Skipping further stages.'
                        currentBuild.result = 'ABORTED'
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
        expression {
            return env.GIT_BRANCH == 'origin/main';
        }
    }

    steps {
        script {
            // Check if the build is aborted, and if so, set the current stage and return
            if (currentBuild.result == 'ABORTED') {
                echo 'No changes in Terraform plan. Skipping further stages.'
                currentBuild.result = 'ABORTED'
                return
            }

            // Run Terraform show and capture the output
            sh "cd \"${WORKSPACE}/${env.Region}\" && terraform show -json tfplan.out > tfplan.json'

            // Run OPA eval
            def opaOutput = sh(script: "opa eval -f pretty -b /cd3user/oci_tools/cd3_automation_toolkit/user-scripts/OPA/ -i \
"${WORKSPACE}/${env.Region}/tfplan.json\" data.terraform.deny", returnStdout: true).trim()    


            if (opaOutput == '[]') {
                     echo "No OPA rules are violated. Proceeding with the next stage."
            } else {
                     echo "OPA rules are violated."
                     echo "OPA Output:\n${opaOutput}"

                     input message: "Do you want to override OPA violations ?"
                     echo "Approval for OPA violations Granted!"

                     //error('OPA rules are violated. Build failed.')
            }

        }
    }
}



       stage('Get Approval') {
    when {
        expression {
            return env.GIT_BRANCH == 'origin/main' && currentBuild.result != 'ABORTED'
        }
    }

    options {
        timeout(time: 10, unit: 'MINUTES')
        }

    steps {
        script {
            if (currentBuild.result == 'ABORTED') {
                echo 'No changes in Terraform plan. Skipping further stages.'
                currentBuild.result = 'ABORTED'
                return
            }

            input message: "Do you want to apply the plan?"
            echo "Approval for the Apply Granted!"
        }
    }
}



        stage('Terraform Apply') {
            when {
                expression {
                    return env.GIT_BRANCH == 'origin/main';
                }
            }

            steps {
                script {
                  // Check if the build is aborted, and if so, set the current stage as SUCCESS and return
                   if (currentBuild.result == 'ABORTED') {
                      echo 'No changes in Terraform plan. Skipping further stages.'
                      currentBuild.result = 'SUCCESS'
                      return
                    }

                    sh "cd \"${WORKSPACE}/${env.Region}\" && terraform apply --auto-approve tfplan.out'
                }
            }
        }
    }
}
