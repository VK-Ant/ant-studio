"""Cloud Storage Output Node — upload results to Azure Blob, S3, GCS."""
import os, json, tempfile
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class CloudStorageOutputNode(BaseNode):
    node_type = "cloud_storage_output"
    label = "Cloud Storage Output"
    category = "output"
    description = "Upload results to Azure Blob, AWS S3, or Google Cloud Storage"
    color = "#059669"

    def define_inputs(self):
        return [
            Port("data", PortType.ANY, "Data to upload"),
            Port("file_path", PortType.TEXT, "Local file to upload (optional)", required=False),
        ]

    def define_outputs(self):
        return [
            Port("upload_url", PortType.TEXT, "Remote URL/path of uploaded file"),
            Port("status", PortType.TEXT, "Upload status"),
        ]

    def define_config(self):
        return [
            NodeConfig("provider", "Cloud Provider", "select", default="azure_blob",
                       options=["azure_blob", "aws_s3", "google_cloud", "minio"]),
            NodeConfig("connection_string", "Connection String / Credentials", "text_area", default=""),
            NodeConfig("container", "Container / Bucket Name", "string", default=""),
            NodeConfig("blob_path", "Destination Path", "string", default="results/output.json"),
            NodeConfig("access_key", "Access Key", "string", default=""),
            NodeConfig("secret_key", "Secret Key", "string", default=""),
            NodeConfig("format", "Output Format", "select", default="json", options=["json", "csv", "raw"]),
        ]

    async def execute(self, inputs, config, context):
        provider = config.get("provider", "azure_blob")
        container = config.get("container", "")
        blob_path = config.get("blob_path", "results/output.json")
        fmt = config.get("format", "json")

        # Prepare local file
        file_path = inputs.get("file_path")
        if not file_path:
            data = inputs.get("data")
            fd, file_path = tempfile.mkstemp(suffix=f".{fmt}")
            with os.fdopen(fd, "w") as f:
                if fmt == "json":
                    json.dump(data, f, indent=2, default=str)
                elif fmt == "csv":
                    import csv
                    rows = [data] if isinstance(data, dict) else data if isinstance(data, list) else [{"result": str(data)}]
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
                    writer.writeheader(); writer.writerows(rows)
                else:
                    f.write(str(data))

        try:
            if provider == "azure_blob":
                from azure.storage.blob import BlobServiceClient
                client = BlobServiceClient.from_connection_string(config.get("connection_string", ""))
                blob_client = client.get_blob_client(container=container, blob=blob_path)
                with open(file_path, "rb") as f:
                    blob_client.upload_blob(f, overwrite=True)
                url = f"azure://{container}/{blob_path}"

            elif provider == "aws_s3":
                import boto3
                s3 = boto3.client("s3", aws_access_key_id=config.get("access_key"),
                                  aws_secret_access_key=config.get("secret_key"))
                s3.upload_file(file_path, container, blob_path)
                url = f"s3://{container}/{blob_path}"

            elif provider == "google_cloud":
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(container)
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(file_path)
                url = f"gs://{container}/{blob_path}"

            elif provider == "minio":
                from minio import Minio
                client = Minio(config.get("connection_string", "localhost:9000"),
                               access_key=config.get("access_key"),
                               secret_key=config.get("secret_key"), secure=False)
                client.fput_object(container, blob_path, file_path)
                url = f"minio://{container}/{blob_path}"
            else:
                url = "unknown"

            return NodeResult(
                outputs={"upload_url": url, "status": "uploaded"},
                message=f"Uploaded to {provider}: {blob_path}",
            )
        except ImportError as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Missing: {e}")
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Upload failed: {e}")
