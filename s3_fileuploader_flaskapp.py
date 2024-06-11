import os
import boto3
from flask import Flask, request, redirect, url_for, render_template_string
import uuid

app = Flask(__name__)

# Initialize the S3 client using environment variables
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
bucket_name = 'rahul.s3.fileuploader'
index_file = 'index.tsv'
tsv_folder = 'tsv/'

# HTML template with Bootstrap for a nicer UI
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload App</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
</head>
<body>
    <div class="container mt-5">
        <h1>Welcome to the File Upload App</h1>
        <p>This app allows you to upload TSV files. The uploaded files will be stored in an S3 bucket, and the details will be recorded in an index file.</p>
        <form method="post" enctype="multipart/form-data" action="/upload">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" class="form-control" name="username" id="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" class="form-control" name="password" id="password" required>
            </div>
            <div class="form-group">
                <label for="file">File:</label>
                <input type="file" class="form-control" name="file" id="file" accept=".tsv" required>
            </div>
            <button type="submit" class="btn btn-primary">Upload</button>
        </form>
    </div>
</body>
</html>
'''

def upload_to_s3(file, bucket, key):
    s3_client.upload_fileobj(file, bucket, key)
    return f"https://{bucket}.s3.amazonaws.com/{key}"

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    username = request.form['username']
    password = request.form['password']
    file = request.files['file']
    
    if not username or not password or not file:
        return "Missing username, password, or file", 400

    # Check file extension
    if not file.filename.endswith('.tsv'):
        return "Only TSV files are allowed", 400

    # Generate a unique filename
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    file_path = tsv_folder + filename

    # Upload the file to S3
    file_url = upload_to_s3(file, bucket_name, file_path)

    # Append user info and file URL to the index file
    index_content = f"{username}\t{password}\t{file_url}\n"
    try:
        index_object = s3_client.get_object(Bucket=bucket_name, Key=index_file)
        existing_index_content = index_object['Body'].read().decode('utf-8')
    except s3_client.exceptions.NoSuchKey:
        existing_index_content = "Username\tPassword\tFile URL\n"  # Adding header
    
    new_index_content = existing_index_content + index_content
    s3_client.put_object(Body=new_index_content, Bucket=bucket_name, Key=index_file, ContentType='text/tab-separated-values')
    
    return f"File uploaded successfully. URL: {file_url}"

if __name__ == '__main__':
    app.run(debug=True)