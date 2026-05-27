pipeline {
    agent any

    stages {

        stage('GitHub Checkout') {
            steps {
                git 'https://github.com/MaheshMelmatti/smart-agri-devsecops.git'
            }
        }

        stage('Docker Build') {
            steps {
                bat 'docker build -t smart-agri ./app'
            }
        }

        stage('Run Docker Container') {
            steps {
                bat 'docker run -d smart-agri'
            }
        }
    }
}