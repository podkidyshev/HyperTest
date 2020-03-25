pipeline {
    agent any

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
                    sh './build.sh'
                }
            }
        }

        stage('run back') {
            steps {
                sh 'echo Launching back'
                sh 'docker-compose -f docker-compose.prod.yaml up -d --build'
                sh 'docker-compose logs'
                sh 'sleep 5'
                sh 'docker-compose logs'
                sh 'docker ps'
            }
        }
    }
}