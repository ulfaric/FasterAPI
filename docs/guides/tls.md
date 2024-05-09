# Setup TLS

Setting up TLS is a painful becuase generating the keys and certificates. Thus, `FAsterAPI` included utility function to do it for you!

## `generate_root_ca()`

:::FasterAPI.utils.generate_root_ca
The above function create a root ca (key and certificate). If a directory is given, the generated files will be saved as PEM format. This should be your first step for server certifcate generation.

## `generate_key_and_csr()`

:::FasterAPI.utils.generate_key_and_csr
The above function generate the private key and certificate signing request for your sever. If a directory is given, both files will be saved as PEM format. Note that, the signing request (CSR) is not a certifcate yet. It must be signed by a CA, which can be the one created by step one or your own.

## `sign_certificate()`

:::FasterAPI.utils.sign_certificate
The above function signs the server certifcate with a CA given by your choice.

## Using TLS

```python
uvicorn.run(
    "FasterAPI.app:app",
    host="0.0.0.0",
    port=PORT,
    ssl_certfile="path/to/server/certifcate",
    ssl_keyfile="path/to/server/key",
)
```
