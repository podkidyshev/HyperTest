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
                        sh 'cat $CRT'
                        sh 'cp $CRT hypertests.crt'
                        sh 'cp $KEY hypertests.key'
                    }
                }
            }
        }

        stage('run back') {
            sh 'echo Stopping previous build'
            sh 'docker-compose down --remove-orphans'

            sh 'echo Launching back'
            sh 'docker-compose -f docker-compose.prod.yaml up -d --build'
        }
    }
}