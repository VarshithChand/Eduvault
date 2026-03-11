pipeline {
    agent any

    environment {
        IMAGE_NAME = "varshithchand/eduvault"
        CONTAINER_NAME = "eduvault"
    }

    stages {

        stage('Clone Repository') {
            steps {
                git 'https://github.com/VarshithChand/Eduvault.git'
            }
        }

        stage('Remove Previous Docker Image') {
            steps {
                sh '''
                docker rmi $IMAGE_NAME:latest || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME:latest .'
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    '''
                }
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                sh 'docker push $IMAGE_NAME:latest'
            }
        }

        stage('Run Container') {
            steps {
                sh '''
                docker rm -f $CONTAINER_NAME || true
                docker run -d -p 5000:5000 --name $CONTAINER_NAME $IMAGE_NAME:latest
                '''
            }
        }
    }
}
