# EVEME

This program is still in development. To build it yourself, you need a firebase realtime database and an ESI endpoint.

1. Create an ESI access point in https://developers.eveonline.com/ with the same scopes present in login.py
2. Copy the client id, secret key, and a randomly generated flask secret key to the variables ESI_CLIENT_ID, ESI_SECRET_KEY, and FLASK_SECRET_KEY in config.py in an instance folder
3. Copy your firebase account info to firebaseAccount.json in the same instance folder. It should contain fields like "private_key_id", "auth_provider_x509_cert_url", etc
4. This was developed on Python 3.8.10+, make sure you're running an venv with that.
5. Run pip install -r requirements.txt
6. Run bin/evemerun. You may need to chmod +x the file before running

# ISSUES

If you don't have the fields already created in your firebase DB (like users, prices, etc) you may need to create them beforehand.

# TODO

1. Deploy on AWS to use anywhere
2. Figure out local caching
3. Figure out if Redis caching is worth it
4. Decide if we need a different database or if firebase is ok. Perhaps s3 for storing profile pictures and something like postgres for storing price data etc?
5. Add feature that lets you paste items and compare total profit if shipped

Build the images and run the containers dev:
```sh
$ docker-compose up -d --build
```
Test it out at http://localhost:5000. The "web" folder is mounted into the container and your code changes apply automatically.

To take it down run
```sh
$ docker-compose down -v
```

Build the images and run the containers prod:
```sh
$ docker-compose -f docker-compose.prod.yml up -d --build
```
Test it out at http://localhost:1337. No mounted folders. To apply changes, the image must be re-built.

To take it down run
```sh
$ docker-compose -f docker-compose.prod.yml down -v
```
