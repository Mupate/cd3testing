/* Set the various stages of the build */
pipeline {
    agent any
    stages {
      stage('Terraform Destroy Plan') {
            when {
      expression {
          return env.GIT_BRANCH == 'origin/main';
      }
        }

    steps {
        script {
                    def jobName = env.JOB_NAME
                    def parts = jobName.split('/')

                    // Assuming the job name format is <region_name>/job/<service_name>/job/job_name
                    def regionName = parts[1]
                    def serviceName = parts[2]

                    // Set environment variables for reuse in subsequent stages
                    env.Region = regionName
                    env.Service = serviceName
        	    
                    sh "cd \"${WORKSPACE}/${env.Region}/${env.Service}\" && terraform init -upgrade"
          	    sh "cd \"${WORKSPACE}/${env.Region}/${env.Service}\" && terraform plan -destroy"
               }
          }
    }

  /** Approval for Terraform Apply **/
   stage('Get Approval') {
            when {
      expression {
          return env.GIT_BRANCH == 'origin/main';
      }
        }
      input {
              message "Do you want to perform terraform destroy?"

    }
      steps {
              echo "Approval for the Destroy Granted!"
          }
      }

      stage('Terraform Destroy') {
            when {
      expression {
          return env.GIT_BRANCH == 'origin/main';
      }
        }

    steps {
        script {
          sh "cd \"${WORKSPACE}/${env.Region}/${env.Service}\" && terraform destroy --auto-approve"
               }
          }
    }

    }
}
