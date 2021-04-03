#!/bin/sh

gpg --quiet --batch --yes --decrypt --passphrase="$SECRET_PASSPHRASE" --output credentials.json credentials.json.gpg