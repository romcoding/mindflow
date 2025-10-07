# MindFlow - Comprehensive Testing Guide

This guide provides step-by-step instructions for testing the full-stack MindFlow application, both locally and after deployment.

## 1. Prerequisites

- **Git**: For cloning the repository.
- **Python 3.11+**: For running the backend.
- **Node.js 18+**: For running the frontend.
- **pnpm**: For frontend package management.
- **GitHub Account**: To access the repository.

## 2. Local Environment Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/romcoding/mindflow.git
    cd mindflow
    ```

2.  **Set up the backend**:

    ```bash
    cd mindflow-backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Set up the frontend**:

    ```bash
    cd ../mindflow-frontend
    pnpm install
    ```

## 3. Running the Application Locally

1.  **Start the backend server** (in a separate terminal):

    ```bash
    cd mindflow-backend
    source venv/bin/activate
    python src/main.py
    ```

    The backend will be running at `http://localhost:5000`.

2.  **Start the frontend development server** (in another terminal):

    ```bash
    cd mindflow-frontend
    pnpm run dev --host
    ```

    The frontend will be accessible at `http://localhost:5173`.

## 4. Testing Scenarios

### 4.1. User Authentication

1.  **Registration**:
    -   Navigate to `http://localhost:5173`.
    -   Click on "Sign Up".
    -   Fill in the registration form with a unique username, email, and a strong password (at least 8 characters with letters and numbers).
    -   Click "Create Account". You should be redirected to the dashboard.

2.  **Login**:
    -   Log out from the dashboard.
    -   You will be redirected to the login page.
    -   Enter the credentials you used for registration.
    -   Click "Sign In". You should be redirected to the dashboard.

3.  **Profile Management**:
    -   On the dashboard, click the settings icon.
    -   Update your first and last name.
    -   Change your password.
    -   Log out and log back in with the new password.

### 4.2. Core Features

1.  **Intelligent Quick Add**:
    -   On the dashboard, click the "QUICK ADD" button.
    -   Type or speak a sentence like: "Remind me to call Alice tomorrow about the project deadline".
    -   Verify that the AI analysis correctly identifies it as a task with the correct priority and due date.
    -   Save the item and check if it appears in the Tasks view.

2.  **Task Management**:
    -   Navigate to the "Tasks" view.
    -   Manually add a new task with a title, description, priority, and due date.
    -   Update an existing task.
    -   Mark a task as complete and verify it moves to the completed list.
    -   Delete a task.

3.  **Stakeholder Management**:
    -   Navigate to the "Stakeholders" view.
    -   Manually add a new stakeholder with detailed personal and professional information.
    -   Click on a stakeholder to view their detailed profile.
    -   Update a stakeholder's information, including their sentiment, influence, and interest.
    -   Verify that the stakeholder map updates accordingly.
    -   Delete a stakeholder.

4.  **Note Taking**:
    -   Navigate to the "Notes" view (once implemented).
    -   Create a new note with a title and content.
    -   Link a note to a stakeholder.
    -   Update and delete notes.

### 4.3. Post-Deployment Testing

Once the application is deployed to Render and Vercel:

1.  Access the frontend URL provided by Vercel.
2.  Repeat all the testing scenarios from section 4.
3.  Verify that the data is persisted in the PostgreSQL database.
4.  Test the application on both desktop and mobile browsers to check for responsiveness.

