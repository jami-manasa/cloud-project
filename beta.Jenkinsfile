def COLOR_MAP = ['SUCCESS': 'good', 'FAILURE': 'danger', 'UNSTABLE': 'danger', 'ABORTED': 'danger']
def remote = [:]
remote.name = "ces-cm-beta"
remote.host = "10.2.0.153"
remote.allowAnyHosts = true
env.ImageName='aws_cm_image_beta'
env.CntrName='aws_cm_cntr'
pipeline {
    options {
     disableConcurrentBuilds(abortPrevious: true)
    }
    agent any
    stages {

        stage('Docker build') {
            steps{
                script{
                    sh 'rm -f $ImageName.tar | true'
                    sh 'cp ~/configs/beta/cm-config.json ./config.json'
                    sh 'ansible-vault decrypt --vault-id ~/.scerets ./config.json'
                    sh 'pwd'
                    sh 'cat config.json'
                    sh 'docker build -t $ImageName .' 
                    sh 'docker container prune -f'
                    sh 'docker images'
                    sh 'docker save -o $ImageName.tar $ImageName' 
                    sh 'chmod 777 $ImageName.tar'
                    sh 'rm -f config.json | true'
                    sh 'ls'
               }
            }
        }

        stage ('Deploy'){
            steps{
        script {
             withCredentials([sshUserPrivateKey(credentialsId: 'ces-cm-beta', keyFileVariable: 'identity', passphraseVariable: '',usernameVariable: 'userName')]) {
             remote.user = userName
             remote.identityFile = identity
            // echo 'Running'
            sshCommand remote: remote, command: 'ls'
            sshCommand remote: remote, command: "docker rm -f ${env.CntrName} | true"
            sshCommand remote: remote, command: "docker rmi ${env.ImageName} | true"
            sshRemove remote: remote, path: "${env.ImageName}.tar"
            sshPut remote: remote, from: "${env.ImageName}.tar", into: '/home/ubuntu/' 
            sshCommand remote: remote, command: "docker load -i ${env.ImageName}.tar"
            sshCommand remote: remote, command: "docker run -itd --name ${env.CntrName} ${env.ImageName}"
            sshRemove remote: remote, path: "${env.ImageName}.tar"
            sshCommand remote: remote, command: "docker update --restart unless-stopped ${env.CntrName}"
        }
    }
            }
        }
    }

    post {
        always {
            echo 'slack notification!'
            slackSend baseUrl: 'https://hooks.slack.com/services/',
            channel: '#jenkins-pipeline-builds', 
            color: COLOR_MAP[currentBuild.currentResult],
            message: "*${currentBuild.currentResult}*: Job ${env.JOB_NAME} build ${env.BUILD_NUMBER} \n More info at: ${env.BUILD_URL}", 
            teamDomain: 'cloudearl',
            tokenCredentialId: 'slack-hook',
            username: 'jenkins-builds'
        }
    }
}


