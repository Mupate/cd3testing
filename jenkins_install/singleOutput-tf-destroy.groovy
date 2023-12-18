properties([
        parameters([
                string(
                        defaultValue: '',
                        name: 'Region',
                        trim: true
                )
        ])
])
/* Set the various stages of the build */
pipeline {
    agent any
    environment {
        CI = 'true'
    }
  stages {
    stage('Terraform Destroy Plan') {
      when {
        expression {
            return env.GIT_BRANCH == 'origin/main';
        }
        }

      steps {
          script {
            sh 'cd ${WORKSPACE}/${Region}/ && terraform init -upgrade'
            sh 'cd ${WORKSPACE}/${Region}/ && terraform plan -destroy'
                 }
            }
        }
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
                echo "Approval for the Terraform Destroy Granted!"
            }
        }

    stage('Terraform Destroy')
          when {
      expression {
          return env.GIT_BRANCH == 'origin/main';
      }
        }

    steps {
        script {
          sh 'cd ${WORKSPACE}/${Region}/ && terraform destroy --auto-approve'
               }
          }
    }
}