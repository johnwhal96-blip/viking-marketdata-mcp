import json
import zlib

from app.viking_client import VikingClient


def test_decode_plain_message():
    raw = json.dumps({"type": "x", "eid": "1", "data": {}})
    assert VikingClient.decode_messages(raw)[0]["eid"] == "1"


def test_decode_compressed_group():
    group = [{"eid": "1"}, {"eid": "2"}]
    compressed = zlib.compress(json.dumps(group).encode())
    assert [item["eid"] for item in VikingClient.decode_messages(compressed)] == ["1", "2"]


def test_extract_points_filters_period_and_bad_rows():
    response = {
        "data": {
            "values": [
                {"dt": 99, "v": 1},
                {"dt": 100, "v": 2},
                {"dt": 150, "v": 3},
                {"dt": 201, "v": 4},
                {"bad": True},
            ]
        }
    }
    assert VikingClient._extract_points(response, 100, 200) == {100: 2, 150: 3}
