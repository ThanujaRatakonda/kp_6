pipeline {
    agent any

    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        HARBOR_URL = "10.131.103.92:8090"
        HARBOR_PROJECT = "kp_4"
        TRIVY_OUTPUT_JSON = "trivy-output.json"
    }

    parameters {
        choice(
            name: 'ACTION',
            choices: ['FULL_PIPELINE', 'FRONTEND', 'BACKEND', 'DATABASE', 'SCALE_ONLY'],
            description: 'Which microservice to build/deploy or just scale'
        )
        string(name: 'FRONTEND_REPLICA', defaultValue: '1', description: 'Frontend replica count')
        string(name: 'BACKEND_REPLICA', defaultValue: '1', description: 'Backend replica count')
        string(name: 'DB_REPLICA', defaultValue: '1', description: 'Database replica count')
    }

    stages {

        stage('Checkout') {
            when { expression { params.ACTION != 'SCALE_ONLY' } }
            steps {
                git url: 'https://github.com/ThanujaRatakonda/kp_4.git', credentialsId: 'githubpat'
            }
        }

        stage('Build Frontend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','FRONTEND'] } }
            steps {
                sh "docker build -t frontend:${IMAGE_TAG} ./frontend"
            }
        }

        stage('Build Backend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','BACKEND'] } }
            steps {
                sh "docker build -t backend:${IMAGE_TAG} ./backend"
            }
        }

        stage('Scan Frontend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','FRONTEND'] } }
            steps {
                sh """
                    trivy image frontend:${IMAGE_TAG} --severity CRITICAL,HIGH --format json -o ${TRIVY_OUTPUT_JSON}
                    jq '[.Results[] |
                        (.Packages // [] | .[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH")) +
                        (.Vulnerabilities // [] | .[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH"))
                    ] | length' ${TRIVY_OUTPUT_JSON}
                """
                archiveArtifacts artifacts: "${TRIVY_OUTPUT_JSON}", fingerprint: true
            }
        }

        stage('Scan Backend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','BACKEND'] } }
            steps {
                sh """
                    trivy image backend:${IMAGE_TAG} --severity CRITICAL,HIGH --format json -o ${TRIVY_OUTPUT_JSON}
                    jq '[.Results[] |
                        (.Packages // [] | .[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH")) +
                        (.Vulnerabilities // [] | .[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH"))
                    ] | length' ${TRIVY_OUTPUT_JSON}
                """
                archiveArtifacts artifacts: "${TRIVY_OUTPUT_JSON}", fingerprint: true
            }
        }

        stage('Push Frontend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','FRONTEND'] } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'harbor-creds', usernameVariable: 'HARBOR_USER', passwordVariable: 'HARBOR_PASS')]) {
                    sh "echo \$HARBOR_PASS | docker login ${HARBOR_URL} -u \$HARBOR_USER --password-stdin"
                    sh "docker tag frontend:${IMAGE_TAG} ${HARBOR_URL}/${HARBOR_PROJECT}/frontend:${IMAGE_TAG}"
                    sh "docker push ${HARBOR_URL}/${HARBOR_PROJECT}/frontend:${IMAGE_TAG}"
                    sh "docker rmi frontend:${IMAGE_TAG} || true"
                }
            }
        }

        stage('Push Backend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','BACKEND'] } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'harbor-creds', usernameVariable: 'HARBOR_USER', passwordVariable: 'HARBOR_PASS')]) {
                    sh "echo \$HARBOR_PASS | docker login ${HARBOR_URL} -u \$HARBOR_USER --password-stdin"
                    sh "docker tag backend:${IMAGE_TAG} ${HARBOR_URL}/${HARBOR_PROJECT}/backend:${IMAGE_TAG}"
                    sh "docker push ${HARBOR_URL}/${HARBOR_PROJECT}/backend:${IMAGE_TAG}"
                    sh "docker rmi backend:${IMAGE_TAG} || true"
                }
            }
        }

        stage('Apply Storage') {
            when { expression { params.ACTION in ['FULL_PIPELINE','DATABASE'] } }
            steps {
                sh "kubectl apply -f k8s/shared-storage-class.yaml"
                sh "kubectl apply -f k8s/shared-pv.yaml"
                sh "kubectl apply -f k8s/shared-pvc.yaml"
            }
        }

        stage('Deploy Database') {
            when { expression { params.ACTION in ['FULL_PIPELINE','DATABASE'] } }
            steps {
                sh "kubectl apply -f k8s/database-deployment.yaml"
            }
        }

        stage('Deploy Frontend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','FRONTEND'] } }
            steps {
                sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/frontend-deployment.yaml"
                sh "kubectl apply -f k8s/frontend-deployment.yaml"
            }
        }

        stage('Deploy Backend') {
            when { expression { params.ACTION in ['FULL_PIPELINE','BACKEND'] } }
            steps {
                sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/backend-deployment.yaml"
                sh "kubectl apply -f k8s/backend-deployment.yaml"
            }
        }

        stage('Scale Deployments') {
            steps {
                script {
                    if(params.ACTION in ['FULL_PIPELINE','FRONTEND','SCALE_ONLY']) {
                        sh "kubectl scale deployment frontend --replicas=${params.FRONTEND_REPLICA}"
                    }
                    if(params.ACTION in ['FULL_PIPELINE','BACKEND','SCALE_ONLY']) {
                        sh "kubectl scale deployment backend --replicas=${params.BACKEND_REPLICA}"
                    }
                    if(params.ACTION in ['FULL_PIPELINE','DATABASE','SCALE_ONLY']) {
                        sh "kubectl scale statefulset database --replicas=${params.DB_REPLICA}"
                    }

                    sh "kubectl get deployments"
                    sh "kubectl get statefulsets"
                }
            }
        }
    }
}
