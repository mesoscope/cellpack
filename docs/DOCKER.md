# Docker

* Install [docker](https://docs.docker.com/v17.09/engine/installation/)
* Clone the repository locally, if you haven't already: `git clone https://github.com/mesoscope/cellpack.git`
* Ensure that you have valid AWS access key and secret to access the `cellpack-results` S3 bucket, usually stored in a `~/.aws/credentials` file. If you have multiple accounts in your credentials files, ensure that the desured account is the `default` option.
*  We have two Dockerfiles in /docker, one that builds the Docker image to be run in AWS ECS, and one to be run in AWS Batch. To build one of the images, run: `docker build -f [DOCKERFILE-NAME] -t [CONTAINER-NAME] .` Rebuild the container if new files are added or changes are made to the codebase.

## AWS Batch Docker Image
1. Build image, running `docker build -f docker/Dockerfile.batch -t [CONTAINER-NAME] .`
2. Run packings in the container, running: `docker run -v ~/.aws:/root/.aws -e recipe=examples/recipes/v2/one_sphere.json -e config=examples/packing-configs/run.json [CONTAINER-NAME]`
3. Verify that the packing results are saved in the `cellpack-results` S3 bucket. You should see a botocore logging message indicating that the credentials were successfully loaded.

## AWS ECS Docker Image
1. Build image, running `docker build -f docker/Dockerfile.ecs -t [CONTAINER-NAME] .`
2. Run packings in the container, running: `docker run -v ~/.aws:/root/.aws -p 80:80 [CONTAINER-NAME]`
3. Try hitting the test endpoint on the server, by navigating to `http://0.0.0.0:8443/hello` in your browser.
4. Try running a packing on the server, by hitting the `http://0.0.0.0:80/pack?recipe=firebase:recipes/one_sphere_v_1.0.0` in your browser.
5. Verify that the packing result path was uploaded to the firebase results table, with the job id specified in the response from the request in step 4.The result simularium file can be found at the s3 path specified there.