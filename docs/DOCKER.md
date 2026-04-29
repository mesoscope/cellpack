# Docker
The CellPACK server, which is used for running packings for [CellPACK Studio](https://github.com/AllenCell/cellpack-client), is run in a Docker container using a Docker image built in this repo.

## Prerequisites
* Install [docker](https://docs.docker.com/v17.09/engine/installation/)
* Clone the repository locally, if you haven't already: `git clone https://github.com/mesoscope/cellpack.git`
* Ensure that you have valid AWS access key and secret to access the `cellpack-results` S3 bucket, usually stored in a `~/.aws/credentials` file. If you have multiple accounts in your credentials files, ensure that the desured account is the `default` option.

## Building and Running the Docker Container
1. Build image, running `docker build -f docker/Dockerfile.ecs -t [CONTAINER-NAME] .`
2. Run packings in the container, running: `docker run -v ~/.aws:/root/.aws -p 80:80 [CONTAINER-NAME]`
3. Try hitting the test endpoint on the server, by navigating to `http://0.0.0.0:80/hello` in your browser.
4. Try running a packing on the server, install and run [CellPACK Studio](https://github.com/AllenCell/cellpack-client) locally, with the [`SUBMIT_PACKING_ECS` constant](https://github.com/AllenCell/cellpack-client/blob/main/src/constants/aws.ts) pointing to your local Docker instance
