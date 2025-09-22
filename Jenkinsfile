pipeline {
    
    agent {
        label "${env.BRANCH_NAME == 'dev_main' ? 'dev-agent' : 'main'}"
    }

    // triggers {
    //     githubPush()  // Trigger build on GitHub push
    //     label "${env.BRANCH_NAME == 'dev_main' ? 'dev-agent' : 'main'}"
    // }

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

        // stage('Inject .env') {
        //     steps {
        //         withCredentials([file(credentialsId: 'gupshup', variable: 'ENV_FILE')]) {
        //             sh 'cp $ENV_FILE .env && cat .env'
        //         }
        //     }
        // }

        stage('Inject .env') {
            steps {
                script {
                // Choose the secret .env strictly by branch
                def envCredId
                switch (env.BRANCH_NAME) {
                    case 'dev_main':
                    envCredId = 'env-file-dev'   // Jenkins "Secret file" credential for DEV
                    break
                    case 'main':
                    envCredId = 'env-file-main'  // Jenkins "Secret file" credential for MAIN/PROD
                    break
                    default:
                    error "Unsupported branch '${env.BRANCH_NAME}'. Only 'dev_main' and 'main' are allowed."
                }

                echo "Using .env from credentials: ${envCredId}"

                withCredentials([file(credentialsId: envCredId, variable: 'ENV_FILE')]) {
                    sh 'cp "$ENV_FILE" .env'
                    // Optional sanity check without leaking secrets:
                    // sh '[ -s .env ] || { echo ".env missing or empty"; exit 1; }'
                }
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

        stage('Stop and Remove Old Docker Container Running on Port 5000') {
            steps {
                sh '''
                    container_id=$(docker ps -q --filter "publish=5000")
                    if [ -n "$container_id" ]; then
                        docker stop $container_id
                        docker rm $container_id
                        echo 'Old container stopped and removed'
                    else
                        echo 'No container running on port 5000'
                    fi
                '''
            }
        }

        stage('Run New Docker Container on Port 5000') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh '''
                        bash -c '
                        export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
                        export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
                        docker run -d -p 5000:5000 \
                            -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
                            -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
                            ${DOCKER_REGISTRY}/${DOCKER_TAG}
                        '
                    '''
                }
            }
        }
    }
    post {
        success {
            slackSend (
                tokenCredentialId: 'slack_channel_secret',
                message: "✅ Build SUCCESSFUL: GUPSHUP${env.JOB_NAME} [${env.BUILD_NUMBER}]",
                channel: '#jenekin_update',
                color: 'good',
                iconEmoji: ':white_check_mark:',
                username: 'Jenkins'
            )
        }
        failure {
            slackSend (
                tokenCredentialId: 'slack_channel_secret',
                message: "❌ Build FAILED: ${env.JOB_NAME} [${env.BUILD_NUMBER}]",
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