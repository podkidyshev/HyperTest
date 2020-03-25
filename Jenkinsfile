pipeline {
    agent any

    stages {
        stage('load ssl') {
            steps {
                withCredentials([
                        file(credentialsId: 'hypertests_crt', variable: 'CRT'),
                        file(credentialsId: 'hypertests_key', variable: 'KEY')
                    ]) {
                    dir('ssl') {
                        sh 'cp ${CRT} hypertests.crt'
                        sh 'cp ${KEY} hypertests.key'
                    }
                }
            }
        }

        stage('load local settings') {
            steps {
                withCredentials([file(credentialsId: 'hypertests_local', variable: 'LOCAL')]) {
                    sh 'cp ${LOCAL} src/settings/local.py'
                    sh 'mv local.py src/settings/local.py'
                }
                sh 'echo Wrote local.py file'
            }
        }

        stage('run back') {
            steps {
                sh 'echo Launching back'
                sh 'docker-compose -f docker-compose.prod.yaml up -d --build'
            }
        }
    }
}