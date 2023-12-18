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
      stage('Terraform Destroy Plan') {
            when {
      expression {
          return env.GIT_BRANCH == 'origin/main';
      }
        }

    steps {
        script {
          sh 'cd ${WORKSPACE}/${Region}/${Service} && terraform init -upgrade'
          sh 'cd ${WORKSPACE}/${Region}/${Service} && terraform plan -destroy'
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
          sh 'cd ${WORKSPACE}/${Region}/${Service} && terraform destroy --auto-approve'
               }
          }
    }

    }
}
