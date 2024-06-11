import os
import boto3
import streamlit as st
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the S3 client using environment variables
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
bucket_name = 'rahul.s3.fileuploader'
index_file = 'index.tsv'
tsv_folder = 'tsv/'

def upload_to_s3(file, bucket, key):
    s3_client.upload_fileobj(file, bucket, key)
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def update_index_file(username, password, file_url):
    index_content = f"{username}\t{password}\t{file_url}\n"
    try:
        index_object = s3_client.get_object(Bucket=bucket_name, Key=index_file)
        existing_index_content = index_object['Body'].read().decode('utf-8')
    except s3_client.exceptions.NoSuchKey:
        existing_index_content = "Username\tPassword\tFile URL\n"  # Adding header
    
    new_index_content = existing_index_content + index_content
    s3_client.put_object(Body=new_index_content, Bucket=bucket_name, Key=index_file, ContentType='text/tab-separated-values')

st.title("File Upload App")
st.write("This app allows you to upload TSV files. The uploaded files will be stored in an S3 bucket, and the details will be recorded in an index file.")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
uploaded_files = st.file_uploader("Choose TSV files", type=["tsv"], accept_multiple_files=True)

if st.button("Upload"):
    if username and password and uploaded_files:
        all_files_uploaded = True
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith('.tsv'):
                # Generate a unique filename
                filename = str(uuid.uuid4()) + os.path.splitext(uploaded_file.name)[1]
                file_path = tsv_folder + filename

                # Upload the file to S3
                try:
                    file_url = upload_to_s3(uploaded_file, bucket_name, file_path)

                    # Update the index file
                    update_index_file(username, password, file_url)
                except Exception as e:
                    st.error(f"Failed to upload {uploaded_file.name}: {str(e)}")
                    all_files_uploaded = False
            else:
                st.error(f"{uploaded_file.name} is not a TSV file")
                all_files_uploaded = False

        if all_files_uploaded:
            st.success("All files uploaded successfully.")
        else:
            st.warning("Some files were not uploaded successfully.")
    else:
        st.error("Please provide all required inputs")