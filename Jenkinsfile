def CM = ['SUCCESS': 'good', 'FAILURE': 'danger', 'UNSTABLE': 'danger', 'ABORTED': 'danger']
def remote = [:]
remote.name = "ces-dev-cm-01"
remote.host = "10.5.1.70"
remote.allowAnyHosts = true
env.ImageName='aws_cm_image'
pipeline {
    options {
     disableConcurrentBuilds(abortPrevious: true)
    }
    

    agent any
    
    stages {
        stage('Clone aws_cm repo') {
             steps {
                script{
                    
                    echo 'Cloning repo'
                    git branch: 'develop', credentialsId: 'jenkins_git_accessd', url: 'https://git.cloudearl.com/solutions/aws_cm.git'
            }
            }
        }
        // stage('copy files to ans-node-01') {
        //     steps {
        //         script{
        //                 echo 'copying'
        //                 sh 'pwd'
        //                 sh 'ls'
        //                 // sh 'chmod 400 cs-dev-web-private.pem'
        //                 // sh 'ansible-playbook -i inventory playbooks/dockerize_repo.yml --limit csdevcm01'
        //               }
        //     }
        // }

        stage('Docker build') {
            steps{
                script{
                    sh 'sudo docker image prune -f'
                    sh 'sudo rm -f $ImageName.tar | true'
                    sh 'cp ~/configs/dev/cm-config.json ./config.json'
                    sh 'ansible-vault decrypt --vault-id ~/.scerets ./config.json'
                    sh 'pwd'
                    sh 'cat config.json'
                    sh 'sudo docker build -t $ImageName .'
                    sh 'sudo docker container prune -f'
                    sh 'sudo docker images'
                    sh 'sudo docker save -o $ImageName.tar $ImageName' 
                    sh 'sudo chmod 777 $ImageName.tar'
                    sh 'ls'      
               }
            }
        }

        stage ('Deploy'){
            steps{
          
            
        
        script {
             withCredentials([sshUserPrivateKey(credentialsId: 'freemium', keyFileVariable: 'identity', passphraseVariable: '',usernameVariable: 'userName')]) {
             remote.user = userName
             remote.identityFile = identity
            echo 'Running'
            sshCommand remote: remote, command: 'ls'
            sshCommand remote: remote, command: 'docker rm -f aws_cm_container | true'
            sshCommand remote: remote, command: 'docker rmi aws_cm_image | true'
            sshRemove remote: remote, path: 'aws_cm_image.tar'
            sshPut remote: remote, from: 'aws_cm_image.tar', into: '/home/ubuntu/' 
            sshCommand remote: remote, command: 'docker load -i aws_cm_image.tar'
            sshCommand remote: remote, command: 'sudo docker run -itd --name aws_cm_container aws_cm_image'
            sshRemove remote: remote, path: 'aws_cm_image.tar'
            sshCommand remote: remote, command: 'sudo docker update --restart unless-stopped aws_cm_container'
        }
    }
            }
        }
            

        
    }

    post {
        always {
            echo 'slack notification!'
        //     slackSend baseUrl: 'https://hooks.slack.com/services/',
        //     channel: '#jenkins-pipeline-builds', 
        //     color: CM[currentBuild.currentResult],
        //     message: "*${currentBuild.currentResult}*: Job ${env.JOB_NAME} build ${env.BUILD_NUMBER} \n More info at: ${env.BUILD_URL}", 
        //     teamDomain: 'cloudearl',
        //     tokenCredentialId: 'slack-hook',
        //     username: 'jenkins-builds'
        }
    }
}


