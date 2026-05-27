pipeline {
    agent any

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'devsecops-pipeline',
                url: 'https://github.com/MaheshMelmatti/smart-agri-devsecops.git'
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