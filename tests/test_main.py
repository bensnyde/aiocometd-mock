import pytest
import time

from aiocometd_mock.cli import parse_args
from aiocometd_mock.server import create_app


@pytest.fixture
def app_args():
    """Returns a standard app with validation enabled."""
    # Create a default args object to pass to create_app
    return parse_args([])


@pytest.fixture
def app(app_args):
    return create_app(app_args)


@pytest.fixture
def non_validating_app(app_args):
    """Returns an app with validation disabled."""
    # Create an args object with the --no-validation flag
    #args = parse_args(["--no-validation"])
    app = create_app(app_args)
    return app


@pytest.fixture
async def cli(aiohttp_client, app):
    """Client for the standard validating app."""
    return await aiohttp_client(app)


@pytest.fixture
async def non_validating_cli(aiohttp_client, non_validating_app):
    """Client for the non-validating app."""
    return await aiohttp_client(non_validating_app)


async def test_handshake(cli):
    payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/handshake"
    assert data[0]["successful"]
    assert "clientId" in data[0]


async def test_connect(cli):
    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # Then, connect with the clientId
    payload = [{"id": "2", "channel": "/meta/connect", "clientId": clientId, "connectionType": "long-polling"}]
    resp = await cli.post("/cometd", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/connect"
    assert data[0]["successful"]


async def test_subscribe(cli):
    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # Then, subscribe with the clientId
    payload = [{"id": "3", "channel": "/meta/subscribe", "clientId": clientId, "subscription": "/foo/bar"}]
    resp = await cli.post("/cometd", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/subscribe"
    assert data[0]["successful"]


async def test_unsubscribe(cli):
    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # Then, unsubscribe with the clientId
    payload = [{"id": "4", "channel": "/meta/unsubscribe", "clientId": clientId, "subscription": "/foo/bar"}]
    resp = await cli.post("/cometd", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/unsubscribe"
    assert data[0]["successful"]


async def test_disconnect(cli):
    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # Then, disconnect with the clientId
    payload = [{"id": "5", "channel": "/meta/disconnect", "clientId": clientId}]
    resp = await cli.post("/cometd", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/disconnect"
    assert data[0]["successful"]


def test_parse_args():
    args = parse_args([
        "--host",
        "127.0.0.1",
        "--port",
        "8888",
        "--expire-client-ids-after",
        "10",
        "--reconnection-interval",
        "20",
    ])
    assert args.host == "127.0.0.1"
    assert args.port == 8888
    assert args.expire_client_ids_after == 10
    assert args.reconnection_interval == 20
    assert not args.no_validation


def test_parse_args_defaults():
    args = parse_args([])
    assert args.host == "localhost"
    assert args.port == 8080
    assert args.expire_client_ids_after is None
    assert args.reconnection_interval == 5
    assert not args.no_validation


def test_parse_args_no_validation():
    args = parse_args(["--no-validation"])
    assert args.host == "localhost"
    assert args.port == 8080
    assert args.no_validation


async def test_connect_reconnect_advice(aiohttp_client):
    args = parse_args(["--reconnection-interval", "2"])
    app = create_app(args)
    cli = await aiohttp_client(app)

    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # First connect should be successful
    connect_payload = [{"id": "2", "channel": "/meta/connect", "clientId": clientId, "connectionType": "long-polling"}]
    resp = await cli.post("/cometd", json=connect_payload)
    data = await resp.json()
    assert "reconnect" not in data[0]["advice"]

    # Second connect should also advise reconnect
    resp = await cli.post("/cometd", json=connect_payload)
    data = await resp.json()
    assert data[0]["advice"]["reconnect"] == "retry"


async def test_connect_reconnect_advice_by_time(aiohttp_client):
    args = parse_args(["--reconnection-interval-seconds", "1"])
    app = create_app(args)
    cli = await aiohttp_client(app)

    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # First connect should be successful
    connect_payload = [{"id": "2", "channel": "/meta/connect", "clientId": clientId, "connectionType": "long-polling"}]
    resp = await cli.post("/cometd", json=connect_payload)
    data = await resp.json()
    assert "reconnect" not in data[0]["advice"]

    # Wait for the reconnection interval to pass
    time.sleep(1)

    # Second connect should also advise reconnect
    resp = await cli.post("/cometd", json=connect_payload)
    data = await resp.json()
    assert data[0]["advice"]["reconnect"] == "retry"


async def test_expire_client_id(aiohttp_client):
    args = parse_args(["--expire-client-ids-after", "1"])
    app = create_app(args)
    cli = await aiohttp_client(app)

    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # First connect should be successful
    connect_payload = [{"id": "2", "channel": "/meta/connect", "clientId": clientId, "connectionType": "long-polling"}]
    resp = await cli.post("/cometd", json=connect_payload)
    assert resp.status == 200

    # Second connect should fail with an unknown clientId error
    resp = await cli.post("/cometd", json=connect_payload)
    assert resp.status == 200

    # Third connect should fail with an unknown clientId error
    resp = await cli.post("/cometd", json=connect_payload)
    assert resp.status == 400
    data = await resp.json()
    assert not data[0]["successful"]
    assert "unknown_client_id" in data[0]["error"]


async def test_expire_client_id_by_time(aiohttp_client):
    args = parse_args(["--expire-client-ids-after-seconds", "1"])
    app = create_app(args)
    cli = await aiohttp_client(app)

    # First, handshake to get a clientId
    handshake_payload = [{"id": "1", "channel": "/meta/handshake"}]
    resp = await cli.post("/cometd", json=handshake_payload)
    data = await resp.json()
    clientId = data[0]["clientId"]

    # First connect should be successful
    connect_payload = [{"id": "2", "channel": "/meta/connect", "clientId": clientId, "connectionType": "long-polling"}]
    resp = await cli.post("/cometd", json=connect_payload)
    assert resp.status == 200

    # Wait for the expiration time to pass
    time.sleep(1)

    # Second connect should fail with an unknown clientId error
    resp = await cli.post("/cometd", json=connect_payload)
    assert resp.status == 200

    # Third connect should fail with an unknown clientId error
    resp = await cli.post("/cometd", json=connect_payload)
    assert resp.status == 400
    data = await resp.json()
    assert not data[0]["successful"]
    assert "unknown_client_id" in data[0]["error"]


async def test_no_validation_flag(aiohttp_client):
    # This payload is invalid because it's missing 'clientId'
    invalid_payload = [{"id": "5", "channel": "/meta/disconnect"}]

    args = parse_args([])
    app = create_app(args)
    cli = await aiohttp_client(app)

    # 1. Test with default client (validation ON) - should fail with 400
    resp_fail = await cli.post("/cometd", json=invalid_payload)
    assert resp_fail.status == 400
    data_fail = await resp_fail.json()
    assert not data_fail[0]["successful"]
    assert "missing_required_fields" in data_fail[0]["error"]

    args = parse_args(["--no-validation"])
    app = create_app(args)
    non_validating_cli = await aiohttp_client(app)

    # 2. Test with non-validating client (validation OFF) - should succeed with 200
    resp_ok = await non_validating_cli.post("/cometd", json=invalid_payload)
    assert resp_ok.status == 200
    data_ok = await resp_ok.json()
    assert data_ok[0]["successful"]
