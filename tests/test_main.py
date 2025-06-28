import pytest

from aiocometd_mock.main import (
    create_app,
    parse_args,
)


@pytest.fixture
def app():
    """Returns a standard app with validation enabled."""
    app = create_app()
    app["no_validation"] = False
    return app


@pytest.fixture
def non_validating_app():
    """Returns an app with validation disabled."""
    app = create_app()
    app["no_validation"] = True
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
    payload = [{"version": "1.0", "supportedConnectionTypes": ["long-polling"]}]
    resp = await cli.post("/cometd/handshake", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/handshake"
    assert data[0]["successful"]
    assert data[0]["supportedConnectionTypes"] == ["long-polling"]


async def test_connect(cli):
    payload = [{"clientId": "test", "connectionType": "long-polling"}]
    resp = await cli.post("/cometd/connect", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/connect"
    assert data[0]["successful"]


async def test_subscribe(cli):
    payload = [{"clientId": "test", "subscription": "/foo/bar"}]
    resp = await cli.post("/cometd/subscribe", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/subscribe"
    assert data[0]["successful"]


async def test_unsubscribe(cli):
    payload = [{"clientId": "test", "subscription": "/foo/bar"}]
    resp = await cli.post("/cometd/unsubscribe", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/unsubscribe"
    assert data[0]["successful"]


async def test_disconnect(cli):
    payload = [{"clientId": "test"}]
    resp = await cli.post("/cometd/disconnect", json=payload)
    assert resp.status == 200
    data = await resp.json()
    assert data[0]["channel"] == "/meta/disconnect"
    assert data[0]["successful"]


def test_parse_args():
    args = parse_args(["--host", "127.0.0.1", "--port", "8888"])
    assert args.host == "127.0.0.1"
    assert args.port == 8888
    assert not args.no_validation


def test_parse_args_defaults():
    args = parse_args([])
    assert args.host == "localhost"
    assert args.port == 8080
    assert not args.no_validation


def test_parse_args_no_validation():
    args = parse_args(["--no-validation"])
    assert args.host == "localhost"
    assert args.port == 8080
    assert args.no_validation


async def test_connect_reconnect_advice(cli):
    # The mock server is stateless and always returns "retry"
    payload = [{"clientId": "test", "connectionType": "long-polling"}]
    resp = await cli.post("/cometd/connect", json=payload)
    data = await resp.json()
    assert data[0]["advice"]["reconnect"] == "retry"


async def test_no_validation_flag(cli, non_validating_cli):
    # This payload is invalid because it's missing 'clientId'
    invalid_payload = [{"channel": "/meta/disconnect"}]

    # 1. Test with default client (validation ON) - should fail with 400
    resp_fail = await cli.post("/cometd/disconnect", json=invalid_payload)
    assert resp_fail.status == 400
    data_fail = await resp_fail.json()
    assert not data_fail[0]["successful"]
    assert "missing_required_fields" in data_fail[0]["error"]

    # 2. Test with non-validating client (validation OFF) - should succeed with 200
    resp_ok = await non_validating_cli.post("/cometd/disconnect", json=invalid_payload)
    assert resp_ok.status == 200
    data_ok = await resp_ok.json()
    assert data_ok[0]["successful"]