pipeline{
    agent any

    triggers {
        githubPush()  // Trigger build on GitHub push
    }

    environment {
        BRANCH_NAME = "${env.BRANCH_NAME}"
        AWS_REGION = 'ap-south-1'
        DOCKER_REGISTRY = '676206929524.dkr.ecr.ap-south-1.amazonaws.com'
        DOCKER_IMAGE = 'dev-orbit-pem'
        DOCKER_NAME = "GUPSHUP"
        DOCKER_TAG = "${DOCKER_IMAGE}:${DOCKER_NAME}${BUILD_NUMBER}"
    }

    stages {
        // Debugging the branch outside any stage
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Inject .env from Jenkins Secret File') {
            steps {
                withCredentials([file(credentialsId: 'gupshup', variable: 'ENV_FILE1')]) {
                    sh 'rm -f .env'
                    sh 'cp $ENV_FILE1 .env'
                }
            }
        }

        stage('Setup Python Env & Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    deactivate
                '''
            }
        }

        stage('Login to AWS ECR') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh '''
                        bash -c '
                        export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
                        export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
                        aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 676206929524.dkr.ecr.ap-south-1.amazonaws.com
                        '
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${DOCKER_TAG} .'
            }
        }

        stage('Tag Docker Image') {
            steps {
                sh 'docker tag ${DOCKER_TAG} ${DOCKER_REGISTRY}/${DOCKER_TAG}'
            }
        }

        stage('Push Docker Image to ECR') {
            steps {
                sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_TAG}'
            }
        }
    }

}