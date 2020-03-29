echo "Cleaning up previous build"
# remove old build
rm -rf ./build
mkdir build

# remove container if somehow exist (due to fail build/run, etc)
docker container stop hypertest_front_container
docker container rm hypertest_front_container

# now fail the whole script if anything fails
set -e

# build image
echo "Building image"
docker image build -t hypertest_front -f Dockerfile .

# build react app
echo "Building react app"
docker run --name=hypertest_front_container hypertest_front npm run build

# copy build to host
echo "Copying files from container to host"
docker cp hypertest_front_container:/app/build .

# cleanup container
echo "Cleaning up container"
docker container stop hypertest_front_container  # ensure to stop the container

set +e
docker container rm hypertest_front_container
