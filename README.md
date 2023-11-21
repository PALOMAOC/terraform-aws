# Terraform Project: AWS Exercise

This Terraform project demonstrates the setup of AWS resources for two exercises:
## 1. Exercise 1: AWS lambda.tf dynamobd.tf ec2.tf roles.tf s3.tf
  - Objective: Trigger a Lambda function every time a JSON file is created in an S3 storage bucket.
  - Key Points: Role creation, S3 bucket creation, DynamoDB table creation, and Lambda function creation.

## 2. Exercise 2: AWS EC2 Instance for Web Visualization
  - Objective: Create a web page to visualize the DynamoDB database.
  - Key Points: EC2 instance creation with security group settings, IAM role creation, and policy attachment for EC2.


# Exercise 1: AWS Lambda Function


## Role Creation
***
To enable interaction between different services, roles must be created to grant them access. First, let's create the roles necessary for the Lambda function by creating the roles.tf file.

```hcl
provider "aws" {
  region = "eu-west-3"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaExecute"
  role       = aws_iam_role.lambda_role.name
}
```
This creates an IAM role for the Lambda function and attaches a policy that allows the execution of Lambda functions.

## S3 Creation
***

At this point, let's create the storage where JSON data for users will be stored. Create the s3.tf file to define the S3 bucket.
```hcl
resource "aws_s3_bucket" "user_data_bucket" {
  bucket = "mi-ejercicio-aws-bucket" 
  acl    = "private"
}
```

## DynamoDB Creation
***

Let's create the DynamoDB table in the dynamodb.tf file.

```hcl
resource "aws_dynamodb_table" "user_data_table" {
  name           = "Usuarios" 
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ID"
  attribute {
    name = "ID"
    type = "N"
  }
}
```

## Lambda Creation
***

With all the above services created, let's finally create the lambda.tf file to define the Lambda function to interact with them..

```hcl
resource "aws_lambda_event_source_mapping" "s3_trigger" {
  event_source_arn  = aws_s3_bucket.user_data_bucket.arn
  function_name     = aws_lambda_function.process_user_data.arn
  starting_position = "LATEST"
  batch_size        = 1
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "lambda_code"
  output_path = "lambda.zip"
}


resource "aws_lambda_function" "process_user_data" {
  function_name    = "process_user_data_lambda"
  runtime          = "python3.8"
  handler          = "lambda_handler.lambda_handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.user_data_table.name
      DEBUG_MODE = "true"
    }
  }
}
```

```python
import json
import boto3
import os

# Creando una instancia de la tabla DynamoD y s3
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Nombre de la tabla en DynamoDB
table = os.environ["TABLE_NAME"]

def lambda_handler(event, context):
    # TODO implement
    print(event)
    # Obtiene el nombre del bucket y la clave del archivo JSON del evento de S3
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(bucket)
    print(key)
    
    # Descarga el archivo JSON desde S3
    response = s3.get_object(Bucket=bucket, Key=key)
    json_data = response['Body'].read().decode('utf-8')

    # Parsea el JSON
    data = json.loads(json_data)

    # Inserta los datos en DynamoDB utilizando el recurso
    response = table.put_item(
        Item={
            'ID': data['ID'],
            'Nombre': data['Nombre'],
            'Correo electrónico': data['Correo electrónico'],
            'Fecha de registro': data['Fecha de registro']
        }
        
    )
    return 
```
With this setup, the lambda function will retrieve data entered into S3 and store it in DynamoDB.

# Exercise 2: AWS EC2 Instance for Web Visualization

## 1. EC2 Creation
***

Create the ec2.tf file for EC2 instance and security group:

archivo ec2.tf:

```hcl

provider "aws" {
  region = "eu-west-3"
}

resource "aws_security_group" "web_sg" {
  name        = "web_security_group"
  description = "Allow inbound traffic on port 8080"

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web_instance" {
  ami           = "ami-00983e8a26e4c9bd9"
  instance_type = "t2.micro"
  key_name      = "key-ssh"

  vpc_security_group_ids = [aws_security_group.web_sg.id]
  tags = {
    Name = "web_instance"
  }

  user_data = <<-EOF
                #!/bin/bash
                sudo apt-get update
                sudo apt-get install -y python3-pip
                
                git clone https://github.com/PALOMAOC/terraform_aws.git /home/ubuntu/tu_app
                cd /home/ubuntu/tu_app/web

                # Instala dependencias
                pip3 install dash boto3
                
                # Ejecuta la aplicación
                nohup python3 /home/ubuntu/app.py > app.log 2>&1 &
              EOF
}

output "public_ip" {
  value = aws_instance.web_instance.public_ip
}
```
Importante asegurarse que la AMI es correcta y de crear la key_name en consola
 
## 2. IAM Role for EC2
***
Create the iam_role_ec2.tf file for IAM role and policy attachment:
```hcl
provider "aws" {
  region = "eu-west-3"
}

resource "aws_iam_role" "ec2_role" {
  name = "ec2_s3_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "s3_write_policy" {
  name        = "s3_write_policy"
  description = "Policy to allow writing to S3"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "s3:PutObject",
        Effect   = "Allow",
        Resource = "*",
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  policy_arn = aws_iam_policy.s3_write_policy.arn
  role       = aws_iam_role.ec2_role.name
}


```


