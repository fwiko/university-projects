FROM nginx:latest
COPY ./ /usr/share/nginx/html/

docker run -it --rm -d -v "$PWD":/usr/share/nginx/html -p 8080:80 --name web webserver