import json
import logging
import os

from urllib.parse import unquote

import azure.functions as func

from azure.storage.blob import BlobServiceClient

memory_bp = func.Blueprint()


@memory_bp.queue_trigger(
    arg_name="azqueue", queue_name="memory", connection="QueueConnectionString"
)
# Comment out below to disable blob input binding
@memory_bp.blob_input(
    arg_name="inputblob",
    path="{image_url}",
    connection="QueueConnectionString",
    data_type="binary",
)
@memory_bp.queue_output(
    arg_name="outputqueue",
    queue_name="memory",
    connection="QueueConnectionString",
)
def memory_queue_main(
    azqueue: func.QueueMessage,
    inputblob: bytes,  # Comment out this line to disable blob input binding
    outputqueue: func.Out[str],
):
    queue_msg = json.loads(azqueue.get_body().decode("utf-8"))
    logging.info(f"Python Queue trigger processed a message: {queue_msg}")

    # Uncomment below to use SDK to download blob

    # logging.info("Downloading blob via SDK")
    # with BlobServiceClient.from_connection_string(
    #     os.environ["QueueConnectionString"]
    # ) as blob_service_client:
    #     inputblob = (
    #         blob_service_client.get_blob_client(
    #             "images", unquote(queue_msg["image_url"]).split("images/")[-1]
    #         )
    #         .download_blob()
    #         .readall()
    #     )

    image_url = queue_msg["image_url"]

    # New queue message
    new_queue_msg = json.dumps({"image_url": image_url})

    # Self queue message
    outputqueue.set(new_queue_msg)
