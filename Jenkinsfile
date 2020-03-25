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
                        sh 'use ${CRT}'
                        sh 'use ${KEY}'
                    }
                }
            }
        }

        stage('load local settings') {
            steps {
                withCredentials([file(credentialsId: 'hypertests_local', variable: 'LOCAL')]) {
//                     sh 'cat ${LOCAL} > src/settings/local.py'
                    sh 'use ${LOCAL}'
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