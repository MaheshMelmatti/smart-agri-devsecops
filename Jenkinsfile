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
                bat 'docker stop smart-agri-container || exit 0'
                bat 'docker rm smart-agri-container || exit 0'
                bat 'docker run -d --name smart-agri-container -p 5000:5000 smart-agri'
            }
        }
    }
}
