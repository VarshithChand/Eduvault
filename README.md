---

# 📚 EduVault

EduVault is a **web-based education resource management platform** that allows users to upload, manage, and share educational documents securely. It helps students and administrators organize study materials in one centralized platform.

---

# 🚀 Features

* 👤 User Authentication
* 📁 Document Upload & Management
* 📂 Organized File Storage
* 🔐 Secure Access Control
* 📊 Simple Dashboard
* 🐳 Docker Containerization
* ⚙️ Jenkins CI/CD Pipeline
* 🔗 GitHub Webhook Integration

---

# 🛠 Tech Stack

### Backend

* Python
* Flask

### Frontend

* HTML
* CSS

### DevOps Tools

* Docker
* Jenkins
* GitHub
* Gunicorn

---

# 📂 Project Structure

```
EduVault
│
├── app.py
├── requirements.txt
├── Dockerfile
├── Jenkinsfile
├── templates/
├── static/
└── README.md
```

---

# ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/VarshithChand/Eduvault.git

cd Eduvault
```

---

### 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Run Application

```bash
python app.py
```

Open in browser:

```
http://localhost:5000
```

---

# 👤 Demo Credentials

### Superuser

```
Username: superuser
Password: 1234
```

### User

```
Username: aa
Password: 1234
```

---

# 🐳 Docker Setup

### Build Image

```bash
docker build -t eduvault .
```

### Run Container

```bash
docker run -d -p 5000:5000 --name eduvault eduvault
```

Application will run at

```
http://localhost:5000
```

---

# 🐳 Run Using Docker Hub Image

Pull image

```bash
docker pull varshithchand/eduvault
```

Run container

```bash
docker run -d -p 5000:5000 varshithchand/eduvault
```

Docker Hub Repository

```
https://hub.docker.com/r/varshithchand/eduvault
```

---

# ⚙️ Jenkins CI/CD Pipeline

This project uses **Jenkins Pipeline** to automate the deployment process.

Pipeline stages:

1️⃣ Clone GitHub repository
2️⃣ Build Docker image
3️⃣ Run Docker container

### Jenkinsfile

```groovy
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

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME .'
            }
        }

        stage('Run Container') {
            steps {
                sh '''
                docker stop $CONTAINER_NAME || true
                docker rm $CONTAINER_NAME || true
                docker run -d -p 5000:5000 --name $CONTAINER_NAME $IMAGE_NAME
                '''
            }
        }
    }
}
```

---

# 🔗 GitHub Webhook Integration

GitHub Webhooks automatically trigger Jenkins builds whenever code is pushed to the repository.

### Step 1 — Configure Jenkins

1. Open Jenkins
2. Go to **Manage Jenkins**
3. Install plugin:

```
GitHub Integration Plugin
```

4. Open your Jenkins job
5. Enable

```
GitHub hook trigger for GITScm polling
```

---

### Step 2 — Configure GitHub Webhook

Open your repository:

```
https://github.com/VarshithChand/Eduvault
```

Go to

```
Settings → Webhooks → Add Webhook
```

Payload URL

```
http://<your-jenkins-server>:8080/github-webhook/
```

Example

```
http://13.201.xxx.xxx:8080/github-webhook/
```

Content type

```
application/json
```

Trigger

```
Just the push event
```

Save webhook.

---

# 🔄 CI/CD Workflow

```
Developer Push Code
        │
        ▼
GitHub Repository
        │
        ▼
GitHub Webhook Trigger
        │
        ▼
Jenkins Pipeline
        │
        ▼
Build Docker Image
        │
        ▼
Run Container
        │
        ▼
Application Deployed
```

---

# 🎯 Future Improvements

* Role-Based Access Control
* File Sharing System
* Search Functionality
* Cloud Storage Integration
* Monitoring with Prometheus & Grafana

---

# 👨‍💻 Author

**Varshith Chand**

GitHub
[https://github.com/VarshithChand](https://github.com/VarshithChand)

Docker Hub
[https://hub.docker.com/r/varshithchand/eduvault](https://hub.docker.com/r/varshithchand/eduvault)

---

# ⭐ Support

If you like this project:

⭐ Star the repository
🍴 Fork the project
📢 Share with others

---

✅ This README now clearly shows **DevOps skills**:

* Docker containerization
* Jenkins pipeline
* GitHub Webhooks
* CI/CD automation

This is **exactly what recruiters look for in DevOps portfolios**.

