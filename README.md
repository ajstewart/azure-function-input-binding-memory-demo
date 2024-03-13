# Azure Function Blob Input Binding Memory Leak Example

This Azure Function is a simple example of a process that causes excessive memory usage, which looks like some kind of leak, when the app is containerised and deployed to kubernetes.

## The Problem Scenario

Excessive memory usage was seen when an input blob binding was used to load the image which was then sent to a endpoint for inference. It is a simple concept queue trigger where:

* Queue message contains inference request info and blob url.
* Blob is loaded via input binding (png image, ~5MB).
* Blob is sent to inference endpoint.
* Request received.
* Event grid and storage tables updated.
* End.

The memory would appear to grow and grow until eventually the deployment memory limit was reached in which case the pod would be restarted. This was seen locally in MiniKube and in Azure Kubernetes Service (AKS).

## The Solution

It was narrowed down to the blob input being the problem. If the binding is removed and instead the Azure Blob Storage SDK is used to load the blob, the memory usage is stable and the problem is resolved.

## This Example Function

This example function is a very basic replica of the problem that also shows large memory usage. It is an endless loop that loads the same blob over and over again. It is a simple way to demonstrate the problem.

It:

* Reads from a queue.
* Uses the blob binding to load the image from blob storage from the message url.
* Sends the same queue message back to the queue.

For testing I used the 5 MB sample png image from <https://sample-videos.com/download-sample-png-image.php>.

A queue message is simply:

```json
{
  "image_url": "url to the blob"
}
```

I put 10 messages in the queue before running.

### Infrastructure

Two storage accounts are required, one for the queue and blob and one for the function WebJobsStorage.

I also used a Application Insights instance to monitor the function.

(I did not try running locally in Docker and using Azurite, as I was in K8s it was easier to create resources)

### Deployment

As I was running in K8s the function was built and pushed to ACR and then deployed to either MiniKube or AKS where KEDA is available, example manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: azure-function-memory-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: azure-function-memory-test
  template:
    metadata:
      labels:
        app: azure-function-memory-test
    spec:
      containers:
      - name: azure-function-memory-test
        image: acrname.azurecr.io/azure-func-memory-test:latest
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 250m
            memory: 1Gi
        env:
        - name: FUNCTIONS_WORKER_RUNTIME
          value: python
        - name: AzureWebJobsFeatureFlags
          value: "EnableWorkerIndexing"
        - name: APPLICATIONINSIGHTS_CONNECTION_STRING
          value: TheConnectionString
        - name: AzureWebJobsStorage
          value: TheConnectionString
        - name: QueueConnectionString
          value: TheConnectionString
      imagePullSecrets:
      - name: dpr-secret

---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: azure-function-memory-test-scaledobject
  namespace: the-namespace
spec:
  scaleTargetRef:
    name: azure-function-memory-test
  minReplicaCount: 1
  maxReplicaCount: 20
  triggers:
  - type: azure-queue
    metadata:
      # Required
      queueName: memory
      # Optional, required when pod identity is used
      accountName: storageaccountname
      # Optional: connection OR authenticationRef that defines connection
      connectionFromEnv: QueueConnectionString # Default: AzureWebJobsStorage. Reference to a connection string in deployment
```

### Switching Between Blob Input and SDK

There are commented out lines in the function to switch between the blob input binding and the SDK, so both can be built and tested.
