# aiocometd-mock

A mock CometD server using `aiohttp` and `asyncio`.

This server implements the basic CometD meta channels (`/meta/handshake`, `/meta/connect`, etc.) and includes request validation to ensure that clients send well-formed messages according to the Bayeux protocol.

## Usage

To start the server, run the following command:

```bash
python main.py
```

By default, the server will run on `localhost:8080`.

### Command-line arguments

You can customize the server's behavior using the following command-line arguments:

  * `--host`: The host to bind to (default: `localhost`).
  * `--port`: The port to bind to (default: `8080`).
  * `--connect-interval`: The connect interval in seconds (default: `60`).
  * `--connect-timeout`: The connect timeout in milliseconds (default: `45000`).
  * `--reconnection-interval`: The reconnection interval in seconds (default: `5`).
  * `--reconnection-interval-seconds`: The reconnection interval in seconds (default: `None`).
  * `--expire-client-ids-after`: The number of connections after which to expire clientIds (default: `None`).
  * `--expire-client-ids-after-seconds`: The number of seconds after which to expire clientIds (default: `None`).
  * `--no-validation`: A flag to disable CometD request validation. When this flag is present, the server will not check for required fields in incoming messages.
  * `--debug`: Enable debug logging.

### Examples

**Run the server on a different host and port:**

```bash
python main.py --host 0.0.0.0 --port 8888
```

**Run the server with request validation disabled:**

```bash
python main.py --no-validation
```

**Run the server with a custom reconnection interval and clientId expiration:**

```bash
python main.py --reconnection-interval 10 --expire-client-ids-after 20
```
