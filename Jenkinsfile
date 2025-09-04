pipeline {
    agent none

    environment {
        AWS_REGION = 'ap-south-1'
        DOCKER_REGISTRY = '676206929524.dkr.ecr.ap-south-1.amazonaws.com'
        DOCKER_IMAGE = 'dev-orbit-pem'
    }

    stages {
        stage('Build & Deploy') {
            agent {
                label "${env.BRANCH_NAME == 'dev' ? 'dev-agent' : 'prod-agent'}"
            }
            stages {
                stage('Checkout') {
                    steps { checkout scm }
                }

                stage('Inject .env') {
                    steps {
                        withCredentials([file(credentialsId: 'gupshup', variable: 'ENV_FILE')]) {
                            sh 'rm -f .env && cp $ENV_FILE .env && cat .env'
                        }
                    }
                }

                stage('Setup Python Env') {
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

                stage('AWS ECR Login') {
                    steps {
                        withCredentials([usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                            sh '''
                                aws ecr get-login-password --region ap-south-1 | \
                                docker login --username AWS --password-stdin 676206929524.dkr.ecr.ap-south-1.amazonaws.com
                            '''
                        }
                    }
                }

                stage('Build, Tag & Push Docker Image') {
                    steps {
                        script {
                            DOCKER_TAG = "${DOCKER_IMAGE}:${env.BRANCH_NAME}-${BUILD_NUMBER}"
                            sh "docker build -t ${DOCKER_TAG} ."
                            sh "docker tag ${DOCKER_TAG} ${DOCKER_REGISTRY}/${DOCKER_TAG}"
                            sh "docker push ${DOCKER_REGISTRY}/${DOCKER_TAG}"
                        }
                    }
                }

                stage('Deploy Container on Port 5000') {
                    steps {
                        sh '''
                            container_id=$(docker ps -q --filter "publish=5000")
                            if [ -n "$container_id" ]; then
                                docker stop $container_id && docker rm $container_id
                            fi
                            docker run -d -p 5000:5000 ${DOCKER_REGISTRY}/${DOCKER_TAG}
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                def slackMsg = "✅ Build SUCCESSFUL: ${env.JOB_NAME} [${env.BUILD_NUMBER}] on branch `${env.BRANCH_NAME}`"
                
                slackSend(
                    tokenCredentialId: 'slack_channel_secret',
                    message: slackMsg,
                    channel: '#jenekin_update',   // single channel
                    color: 'good',
                    iconEmoji: ':white_check_mark:',
                    username: 'Jenkins'
                )
            }
        }

        failure {
            script {
                def slackMsg = "❌ Build FAILED: ${env.JOB_NAME} [${env.BUILD_NUMBER}] on branch `${env.BRANCH_NAME}`"
                
                slackSend(
                    tokenCredentialId: 'slack_channel_secret',
                    message: slackMsg,
                    channel: '#jenekin_update',   // same single channel
                    color: 'danger',
                    iconEmoji: ':x:',
                    username: 'Jenkins'
                )
            }
        }

        always {
            cleanWs()
        }
    }
}
