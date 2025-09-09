pipeline {
    // Choose agent based on the branch name. The `env.BRANCH_NAME` is
    // automatically available in a Multibranch Pipeline.
    agent {
        label "${env.BRANCH_NAME == 'dev_main' ? 'dev-agent' : ''}"
    }
    

    environment {
        AWS_REGION      = 'ap-south-1'
        DOCKER_REGISTRY = '676206929524.dkr.ecr.ap-south-1.amazonaws.com'
        DOCKER_IMAGE    = 'dev-orbit-pem'
    }

    stages {
        stage('Checkout') {
            steps {
                // `checkout scm` is sufficient for Multibranch Pipelines.
                checkout scm
                echo "Branch detected: ${env.BRANCH_NAME}"
            }
        }

        stage('Inject .env') {
            steps {
                withCredentials([file(credentialsId: 'gupshup', variable: 'ENV_FILE')]) {
                    sh 'cp $ENV_FILE .env && cat .env'
                }
            }
        }
        

        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('AWS ECR Login') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}"
                }
            }
        }

        stage('Build, Tag & Push Docker Image') {
            steps {
                script {
                    env.DOCKER_TAG = "${DOCKER_IMAGE}:${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
                    sh "docker build -t ${env.DOCKER_TAG} ."
                    sh "docker tag ${env.DOCKER_TAG} ${DOCKER_REGISTRY}/${env.DOCKER_TAG}"
                    sh "docker push ${DOCKER_REGISTRY}/${env.DOCKER_TAG}"
                }
            }
        }

        stage('Deploy Container') {
            steps {
                sh '''
                    # Add a check to handle existing containers
                    if [ $(docker ps -q -f name=my-app-container) ]; then
                        docker stop my-app-container
                        docker rm my-app-container
                    fi
                    docker run -d --name my-app-container -p 5000:5000 ${DOCKER_REGISTRY}/${DOCKER_TAG}
                '''
            }
        }
    }


    post {
        success {
            slackSend(
                tokenCredentialId: 'slack_channel_secret',
                message: "✅ Build SUCCESSFUL: ${env.JOB_NAME} [${env.BUILD_NUMBER}] on branch `${env.BRANCH_NAME}`",
                channel: '#jenekin_update',
                color: 'good',
                iconEmoji: ':white_check_mark:',
                username: 'Jenkins'
            )
        }
        failure {
            slackSend(
                tokenCredentialId: 'slack_channel_secret',
                message: "❌ Build FAILED: ${env.JOB_NAME} [${env.BUILD_NUMBER}] on branch `${env.BRANCH_NAME}`",
                channel: '#jenekin_update',
                color: 'danger',
                iconEmoji: ':x:',
                username: 'Jenkins'
            )
        }
        always {
            cleanWs()
        }
    }
}