"""FTP/SFTP Input Node."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class FTPInputNode(BaseNode):
    node_type = "ftp_input"
    label = "FTP/SFTP Input"
    category = "input"
    description = "Download files from FTP or SFTP server"
    color = "#6366f1"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [
            Port("file_path", PortType.TEXT, "Local path to downloaded file"),
            Port("file_name", PortType.TEXT, "File name"),
        ]

    def define_config(self):
        return [
            NodeConfig("protocol", "Protocol", "select", default="sftp", options=["ftp", "sftp"]),
            NodeConfig("host", "Host", "string", default=""),
            NodeConfig("port", "Port", "number", default=22),
            NodeConfig("username", "Username", "string", default=""),
            NodeConfig("password", "Password", "string", default=""),
            NodeConfig("remote_path", "Remote File Path", "string", default="/documents/file.pdf"),
            NodeConfig("download_dir", "Local Download Dir", "string", default="./data/downloads"),
        ]

    async def execute(self, inputs, config, context):
        protocol = config.get("protocol", "sftp")
        host = config.get("host", "")
        remote_path = config.get("remote_path", "")
        download_dir = config.get("download_dir", "./data/downloads")
        os.makedirs(download_dir, exist_ok=True)
        local_path = os.path.join(download_dir, os.path.basename(remote_path))

        try:
            if protocol == "sftp":
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=int(config.get("port", 22)),
                            username=config.get("username"), password=config.get("password"))
                sftp = ssh.open_sftp()
                sftp.get(remote_path, local_path)
                sftp.close(); ssh.close()
            else:
                from ftplib import FTP
                ftp = FTP()
                ftp.connect(host, int(config.get("port", 21)))
                ftp.login(config.get("username", ""), config.get("password", ""))
                with open(local_path, "wb") as f:
                    ftp.retrbinary(f"RETR {remote_path}", f.write)
                ftp.quit()

            return NodeResult(
                outputs={"file_path": local_path, "file_name": os.path.basename(remote_path)},
                message=f"Downloaded via {protocol}: {os.path.basename(remote_path)}",
            )
        except ImportError as e:
            msg = "pip install paramiko" if protocol == "sftp" else str(e)
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=msg)
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"{protocol} error: {e}")
