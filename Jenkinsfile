pipeline {
agent any

```
stages {

    stage('GitHub Checkout') {
        steps {
            git branch: 'devsecops-pipeline',
                url: 'https://github.com/MaheshMelmatti/smart-agri-devsecops.git'
        }
    }

    stage('Docker Build') {
        steps {
            sh '''
            docker build -t smart-agri ./app
            '''
        }
    }

    stage('Stop Old Container') {
        steps {
            sh '''
            docker stop smart-agri-container || true
            docker rm smart-agri-container || true
            '''
        }
    }

    stage('Run Docker Container') {
        steps {
            sh '''
            docker run -d \
            --name smart-agri-container \
            -p 5000:5000 \
            smart-agri
            '''
        }
    }

    stage('Verify Deployment') {
        steps {
            sh '''
            docker ps
            '''
        }
    }
}

post {
    success {
        echo 'Build and Deployment Successful!'
    }

    failure {
        echo 'Build Failed!'
    }
}
```

}
