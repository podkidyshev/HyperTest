pipeline {
    agent any

    stages {
        stage('stop previous') {
            steps {
                sh 'echo Stopping previous build'
                sh 'docker-compose down --remove-orphans'
                sh 'ls'
            }
        }

        stage('load ssl') {
            steps {
                withCredentials([
                        file(credentialsId: 'hypertests_crt', variable: 'CRT'),
                        file(credentialsId: 'hypertests_key', variable: 'KEY')
                    ]) {
                    dir('ssl') {
                        sh 'cat $CRT > hypertests.crt'
                        sh 'cat $KEY > hypertests.key'
                    }
                }
            }
        }

        stage('load local settings') {
            steps {
                withCredentials([file(credentialsId: 'hypertests_local', variable: 'LOCAL')]) {
                    sh 'cat $LOCAL > src/settings/local.py'
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