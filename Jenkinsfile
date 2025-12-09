pipeline {
    agent any

    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        HARBOR_URL = "10.131.103.92:8090"
        HARBOR_PROJECT = "kp_4"
        TRIVY_OUTPUT_JSON = "trivy-output.json"
    }

    parameters {
        choice(name: 'ACTION', choices: ['FULL_PIPELINE', 'SCALE_ONLY'])
        string(name: 'REPLICA_COUNT', defaultValue: '1')
        string(name: 'DB_REPLICA_COUNT', defaultValue: '1')
    }

    stages {

        stage('Checkout') {
            when { expression { params.ACTION == 'FULL_PIPELINE' } }
            steps {
                git 'https://github.com/ThanujaRatakonda/kp_4.git'
            }
        }

        stage('Detect Changes') {
            when { expression { params.ACTION == 'FULL_PIPELINE' } }
            steps {
                script {
                    echo "Detecting changes for frontend and backend..."

                    env.CHANGED_FRONTEND = sh(
                        script: "git diff --name-only HEAD~1 HEAD | grep '^frontend/' || true",
                        returnStdout: true
                    ).trim()

                    env.CHANGED_BACKEND = sh(
                        script: "git diff --name-only HEAD~1 HEAD | grep '^backend/' || true",
                        returnStdout: true
                    ).trim()

                    if (!env.CHANGED_FRONTEND && !env.CHANGED_BACKEND) {
                        error "No changes detected → Skipping pipeline."
                    }

                    echo "Frontend changed: ${env.CHANGED_FRONTEND != ''}"
                    echo "Backend changed: ${env.CHANGED_BACKEND != ''}"
                }
            }
        }

        stage('Build Docker Images') {
            when { expression { params.ACTION == 'FULL_PIPELINE' } }
            steps {
                script {
                    if (env.CHANGED_FRONTEND) {
                        sh "docker build -t frontend:${IMAGE_TAG} ./frontend"
                    }
                    if (env.CHANGED_BACKEND) {
                        sh "docker build -t backend:${IMAGE_TAG} ./backend"
                    }
                }
            }
        }

        stage('Scan Docker Images') {
            when { expression { params.ACTION == 'FULL_PIPELINE' } }
            steps {
                script {
                    if (env.CHANGED_FRONTEND) {
                        sh """
                            trivy image frontend:${IMAGE_TAG} \
                            --severity CRITICAL,HIGH \
                            --format json \
                            -o ${TRIVY_OUTPUT_JSON}
                        """
                    }

                    if (env.CHANGED_BACKEND) {
                        sh """
                            trivy image backend:${IMAGE_TAG} \
                            --severity CRITICAL,HIGH \
                            --format json \
                            -o ${TRIVY_OUTPUT_JSON}
                        """
                    }
                }
            }
        }

        stage('Push Images to Harbor') {
            when { expression { params.ACTION == 'FULL_PIPELINE' } }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'harbor-creds', usernameVariable: 'HARBOR_USER', passwordVariable: 'HARBOR_PASS')]) {
                        sh "echo \$HARBOR_PASS | docker login ${HARBOR_URL} -u \$HARBOR_USER --password-stdin"
                    }

                    if (env.CHANGED_FRONTEND) {
                        sh """
                            docker tag frontend:${IMAGE_TAG} ${HARBOR_URL}/${HARBOR_PROJECT}/frontend:${IMAGE_TAG}
                            docker push ${HARBOR_URL}/${HARBOR_PROJECT}/frontend:${IMAGE_TAG}
                        """
                    }

                    if (env.CHANGED_BACKEND) {
                        sh """
                            docker tag backend:${IMAGE_TAG} ${HARBOR_URL}/${HARBOR_PROJECT}/backend:${IMAGE_TAG}
                            docker push ${HARBOR_URL}/${HARBOR_PROJECT}/backend:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Apply Kubernetes Deployment') {
            when { expression { params.ACTION == 'FULL_PIPELINE' } }
            steps {
                script {

                    if (env.CHANGED_FRONTEND) {
                        sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/frontend-deployment.yaml"
                        sh "kubectl apply -f k8s/frontend-deployment.yaml"
                    }

                    if (env.CHANGED_BACKEND) {
                        sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/backend-deployment.yaml"
                        sh "kubectl apply -f k8s/backend-deployment.yaml"
                    }

                    // database always applied (image never changes)
                    sh "kubectl apply -f k8s/database-deployment.yaml"
                    sh """
                    kubectl get sc shared-storage-class || kubectl apply -f k8s/shared-storage-class.yaml
                    kubectl get pv shared-pv || kubectl apply -f k8s/shared-pv.yaml
                    kubectl get pvc shared-pvc || kubectl apply -f k8s/shared-pvc.yaml
                    """
                }
            }
        }

        stage('Scale Deployments') {
            steps {
                script {
                    sh "kubectl scale deployment frontend --replicas=${params.REPLICA_COUNT}"
                    sh "kubectl scale deployment backend --replicas=${params.REPLICA_COUNT}"
                    sh "kubectl scale statefulset database --replicas=${params.DB_REPLICA_COUNT}"
                    sh "kubectl get deployments"
                }
            }
        }
    }
}
