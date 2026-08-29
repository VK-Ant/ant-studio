"""Cloud Storage Input Node — Azure Blob, AWS S3, Google Cloud Storage."""
import os, tempfile
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class CloudStorageInputNode(BaseNode):
    node_type = "cloud_storage_input"
    label = "Cloud Storage Input"
    category = "input"
    description = "Download files from Azure Blob, AWS S3, or Google Cloud Storage"
    color = "#6366f1"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [
            Port("file_path", PortType.TEXT, "Local path to downloaded file"),
            Port("file_name", PortType.TEXT, "Original file name"),
            Port("content", PortType.TEXT, "File content (text files only)"),
            Port("file_size", PortType.FLOAT, "File size in bytes"),
        ]

    def define_config(self):
        return [
            NodeConfig("provider", "Cloud Provider", "select", default="azure_blob",
                       options=["azure_blob", "aws_s3", "google_cloud", "minio"]),
            NodeConfig("connection_string", "Connection String / Credentials", "text_area", default=""),
            NodeConfig("container", "Container / Bucket Name", "string", default=""),
            NodeConfig("blob_path", "Blob / Object Path", "string", default="documents/invoice.pdf"),
            NodeConfig("region", "Region (AWS/GCS)", "string", default="us-east-1"),
            NodeConfig("access_key", "Access Key / Account Name", "string", default=""),
            NodeConfig("secret_key", "Secret Key / Account Key", "string", default=""),
            NodeConfig("download_dir", "Local Download Directory", "string", default="./data/downloads"),
        ]

    async def execute(self, inputs, config, context):
        provider = config.get("provider", "azure_blob")
        container = config.get("container", "")
        blob_path = config.get("blob_path", "")
        download_dir = config.get("download_dir", "./data/downloads")
        os.makedirs(download_dir, exist_ok=True)
        local_path = os.path.join(download_dir, os.path.basename(blob_path))

        try:
            if provider == "azure_blob":
                try:
                    from azure.storage.blob import BlobServiceClient
                    conn_str = config.get("connection_string", "")
                    client = BlobServiceClient.from_connection_string(conn_str)
                    blob_client = client.get_blob_client(container=container, blob=blob_path)
                    with open(local_path, "wb") as f:
                        data = blob_client.download_blob().readall()
                        f.write(data)
                except ImportError:
                    return NodeResult(outputs={}, status=NodeStatus.ERROR,
                                      message="pip install azure-storage-blob")

            elif provider == "aws_s3":
                try:
                    import boto3
                    s3 = boto3.client("s3",
                                      aws_access_key_id=config.get("access_key"),
                                      aws_secret_access_key=config.get("secret_key"),
                                      region_name=config.get("region", "us-east-1"))
                    s3.download_file(container, blob_path, local_path)
                except ImportError:
                    return NodeResult(outputs={}, status=NodeStatus.ERROR, message="pip install boto3")

            elif provider == "google_cloud":
                try:
                    from google.cloud import storage
                    client = storage.Client()
                    bucket = client.bucket(container)
                    blob = bucket.blob(blob_path)
                    blob.download_to_filename(local_path)
                except ImportError:
                    return NodeResult(outputs={}, status=NodeStatus.ERROR,
                                      message="pip install google-cloud-storage")

            elif provider == "minio":
                try:
                    from minio import Minio
                    client = Minio(config.get("connection_string", "localhost:9000"),
                                   access_key=config.get("access_key"),
                                   secret_key=config.get("secret_key"), secure=False)
                    client.fget_object(container, blob_path, local_path)
                except ImportError:
                    return NodeResult(outputs={}, status=NodeStatus.ERROR, message="pip install minio")

            # Read content for text files
            content = ""
            try:
                if any(local_path.lower().endswith(e) for e in [".txt", ".md", ".csv", ".json", ".xml"]):
                    with open(local_path, "r", errors="ignore") as f:
                        content = f.read()
            except Exception:
                pass

            return NodeResult(
                outputs={"file_path": local_path, "file_name": os.path.basename(blob_path),
                          "content": content, "file_size": os.path.getsize(local_path)},
                message=f"Downloaded from {provider}: {os.path.basename(blob_path)}",
            )
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"{provider} error: {e}")
