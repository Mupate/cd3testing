properties([
    parameters([
        string(
            defaultValue: '',
            name: 'Region',
            trim: true
        ),
        string(
            defaultValue: '',
            name: 'Service',
            trim: true,
        )
    ])
])

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
                    sh 'cd ${WORKSPACE}/${Region}/${Service} && terraform init -upgrade'

                    // Run Terraform plan and capture the output
                    def terraformPlanOutput = sh(script: 'cd ${WORKSPACE}/${Region}/${Service} && terraform plan -out=tfplan.out', returnStdout: true).trim()

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
            sh 'cd ${WORKSPACE}/${Region}/${Service} && terraform show -json tfplan.out > tfplan.json'

            // Run OPA eval
            def opaOutput = sh(
                script: 'opa eval -f pretty -b /cd3user/oci_tools/cd3_automation_toolkit/user-scripts/OPA/ -i ${WORKSPACE}/${Region}/${Service}/tfplan.json data.terraform.deny',
                returnStdout: true
            ).trim()

 
            if (opaOutput == '[]') {
                     echo "No OPA rules are violated. Proceeding with the next stage."
            } else {
                     echo "OPA rules are violated."
                     echo "OPA Output:\n${opaOutput}"

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

                    sh 'cd ${WORKSPACE}/${Region}/${Service} && terraform apply --auto-approve tfplan.out'
                }
            }
        }
    }
}

