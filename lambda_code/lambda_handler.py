import json
import boto3
import os

# Creando instancias de tabla DynamoDB y S3
s3 = boto3.client('s3', region_name="eu-west-3")
dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')

# Nombre de la tabla en DynamoDB
table = os.environ["TABLE_NAME"]

def lambda_handler(event, context):
    # Obtiene el nombre del bucket y la clave del archivo JSON del evento de S3
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Descarga el archivo JSON desde S3
    response = s3.get_object(Bucket=bucket, Key=key)
    json_data = response['Body'].read().decode('utf-8')

    # Parsea el JSON
    data = json.loads(json_data)

    # Inserta los datos en DynamoDB
    response = table.put_item(
        Item={
            'ID': data['ID'],
            'Nombre': data['Nombre'],
            'Correo electrónico': data['Correo electrónico'],
            'Fecha de registro': data['Fecha de registro']
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps('Datos guardados en DynamoDB exitosamente.')
    }