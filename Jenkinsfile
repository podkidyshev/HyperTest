// required_params:
//   - deploy_ip - host ip or name to deploy (using ssh)
//   - deploy_path - path on remote host to deploy
pipeline {
    agent any

    stages {
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
                sh 'cp docker/front/prod/* front/'
                dir('front') {
                    sh 'bash ./build.sh'
                }
                sh 'mv front/build front-build && rm -rf front/* && mv front-build front/build'
            }
        }

        stage('make artifacts') {
            steps {
                sh 'tar -czf artifacts.tar.gz ssl/ docs/ front/ src/ docker* requirements/ setup-prod.sh Dockerfile Jenkinsfile'
            }
        }

        stage('deploy') {
            steps {
                script {
                    withCredentials([sshUserPrivateKey(credentialsId: 'hypertests_ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                        sh "ssh -o StrictHostKeyChecking=no -i ${SSH_KEY} ${SSH_USER}@hypertests.ru '\
                            mkdir -p ~/Projects/hypertest'"
                        sh "scp -o StrictHostKeyChecking=no -i ${SSH_KEY} artifacts.tar.gz ${SSH_USER}@hypertests.ru:~/Projects/hypertest"
                        sh "ssh -o StrictHostKeyChecking=no -i ${SSH_KEY} ${SSH_USER}@hypertests.ru '\
                            cd Projects/hypertest && \
                            ls && \
                            ./setup-prod.sh && \
                            docker-compose down --remove-orphans && \
                            docker-compose rm && \
                            rm -rf docs/ front/ src/ docker* requirements/ Dockerfile Jenkinsfile && \
                            gunzip -c artifacts.tar.gz | tar xopf - && \
                            rm -rf artifacts.tar.gz && \
                            ls && \
                            docker-compose up -d --build && \
                            docker-compose logs && \
                            sleep 5 && \
                            docker-compose logs && \
                            docker ps && \
                            echo successfully deployed'"
                    }
                }
            }
        }
    }
}