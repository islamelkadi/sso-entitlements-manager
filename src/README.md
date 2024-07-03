# Regex rules engine

This directory contains the source code for the regex rules engine microservices. The repo contains the following files & folders:

- app - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code.
- template.yaml - A template that defines the application's AWS resources.

## Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

```bash
regex_rules$ sam build --use-container
```

The SAM CLI installs dependencies defined in `app/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
regex_rules$ sam local invoke HelloWorldFunction --event events/event.json
```

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

```bash
regex_rules$ sam local start-api
regex_rules$ curl http://localhost:3000/
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. The `Events` property on each function's definition includes the route and method for each path.

```yaml
      Events:
        HealthCheck:
          Type: Api
          Properties:
            Path: /hello
            Method: get
```
