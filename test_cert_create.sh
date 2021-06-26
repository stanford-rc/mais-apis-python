#!/bin/bash



# Exit on undefined variables.  These should be caught in dev, so set early.
set -u

# Create temporary files.  If we fail, clean up the ones that have
# already been created.
temp_key=$(mktemp keyXXXXXX.pem)
if [ $? -ne 0 ]; then
    echo "$0: Can't create temp file.  Exiting."
    exit 1
fi
temp_cert=$(mktemp certXXXXXX.pem)
if [ $? -ne 0 ]; then
    echo "$0: Can't create temp file.  Exiting."
    rm ${temp_key}
    exit 1
fi
temp_config=$(mktemp configXXXXXX.pem)
if [ $? -ne 0 ]; then
    echo "$0: Can't create temp file.  Exiting."
    rm ${temp_cert}
    rm ${temp_key}
    exit 1
fi

# Now we have all three files created, make a cleanup routine, and set it
# to run on exit.
function cleanup {
    rm ${temp_key}
    rm ${temp_cert}
    rm ${temp_config}
}
trap cleanup EXIT

# Now it's safe to die on errors!
set -e

# Write out our OpenSSL config.
cat - > ${temp_config} <<EOF
[ req_distinguished_name ]
[ req ]
distinguished_name = req_distinguished_name
EOF

# Make the things!

echo "Generating private key"
openssl ecparam -genkey -name P-256 -out ${temp_key}

echo "Generating cert"
openssl req -config ${temp_config} -new -key ${temp_key} -x509 -subj '/CN=snakeoil' -days +7305 -out ${temp_cert}

# Output the things!
echo 'Your test key/cert consists of three blocks.'
echo 'Please paste all of them, in order, into your code.'
cat ${temp_key}
cat ${temp_cert}

# All done!
# (Remember, our function will do cleanup).
exit 0
