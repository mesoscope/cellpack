# Remote Databases 
## AWS S3
1. Pre-requisites
   * Obtain an AWS account for AICS. Please contact the IT team or the code owner. 
   * Generate an `aws_access_key_id` and `aws_secret_access_key` in your AWS account.

2. Step-by-step Guide
   * Download and install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
   * Configure AWS CLI by running `aws configure`, then enter your credentials as prompted.
   * Ensure that Boto3, the AWS SDK for Python is installed and included in the requirements section of `setup.py`. 

## Firebase Firestore
1. Step-by-step Guide
   * For dev database:
     * Create a Firebase project in test mode with your google account, select `firebase_admin` as the SDK. [Firebase Firestore tutorial](https://firebase.google.com/docs/firestore)
     * Generate a new private key by navigating to "Project settings">"Service account" in the project's dashboard.
   * For staging database:
       * Obtain credentials:
          * Reach out to the code owner for the necessary credentials.
       * Configure the environment variables:
          * Create a `.env` file in the root directory.
          * Populate the `.env` file with the following variables:
           ```
               FIREBASE_TOKEN=KEY_JSON_FILE["private_key"]
               FIREBASE_EMAIL=KEY_JSON_FILE["client_email"]
           ```
          note: `KEY_JSON_FILE` is the content of the private key JSON file generated in the staging Firebase.