pipeline {
    agent any

    def remote = [:]
    remote.name = 'hypertests'
    remote.host = 'hypertests.ru'
    remote.allowAnyHosts = true

    stages {
        stage('cleanup') {
            steps {
                sh 'docker-compose down --remove-orphans'
                sh 'docker-compose rm'
            }
        }

        stage('checkout front') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    userRemoteConfigs: [[url: 'https://github.com/artemykairyak/hyperTest.git']],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'front']]])
            }
        }

        stage('load ssl') {
            steps {
                withCredentials([
                        file(credentialsId: 'hypertests_crt', variable: 'CRT'),
                        file(credentialsId: 'hypertests_key', variable: 'KEY')
                    ]) {
                    dir('ssl') {
                        sh 'cat ${CRT} > hypertests.crt'
                        sh 'cat ${KEY} > hypertests.key'
                    }
                }
            }
        }

        stage('load local settings') {
            steps {
                withCredentials([file(credentialsId: 'hypertests_local', variable: 'LOCAL')]) {
                    sh 'cat ${LOCAL} > src/settings/local.py'
                }
                sh 'echo Wrote local.py file'
            }
        }

        stage('build front') {
            steps {
                sh 'cp docker/front/* front/'
                dir('front') {
                    sh 'bash ./build.sh'
                }
            }
        }

        stage('deploy') {
            withCredentials([sshUserPrivateKey(credentialsId: 'hypertests_ssh', keyFileVariable: 'SSH_KEY', passphraseVariable: 'SSH_PHRASE', usernameVariable: 'SSH_USER')]) {
                remote.user = SSH_USER
                remote.identityFile = SSH_KEY

                // mkdir if not exist
                sshCommand remote: remote, command: 'mkdir -p ~/Projects/hypertests'
                // copy files
                sshPut remote: remote, from: 'front/ src/ docker* requirements/ Dockerfile Jenkinsfile', into: '~/Projects/hypertests/'
                sshCommand remote: remote, command: 'docker-compose -f docker-compose.prod.yaml up -d --build && \
                    docker-compose logs && sleep 5 && docker-compose logs && docker ps && echo successfully deployed'
            }
        }

//         stage('run back') {
//             steps {
//                 sh 'echo Launching back'
//                 sh 'docker-compose -f docker-compose.prod.yaml up -d --build'
//                 sh 'docker-compose logs'
//                 sh 'sleep 5'
//                 sh 'docker-compose logs'
//                 sh 'docker ps'
//                 sh 'echo success!'
//             }
//         }
    }
}