import re

import pytest

from cognite.client.data_classes import Label, LabelDefinition, LabelDefinitionList
from tests.utils import jsgz_load


@pytest.fixture
def mock_labels_response(rsps, cognite_client):
    response_body = {
        "items": [
            {"name": "Pump", "description": "guess", "externalId": "PUMP", "createdTime": 1575892259245, "dataSetId": 1}
        ]
    }

    url_pattern = re.compile(re.escape(cognite_client.labels._get_base_url_with_base_path()) + "/.+")
    rsps.assert_all_requests_are_fired = False

    rsps.add(rsps.POST, url_pattern, status=200, json=response_body)
    rsps.add(rsps.GET, url_pattern, status=200, json=response_body)
    yield rsps


class TestLabels:
    def test_list(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.list(external_id_prefix="P")
        assert "P" == jsgz_load(mock_labels_response.calls[0].request.body)["filter"]["externalIdPrefix"]
        assert mock_labels_response.calls[0].response.json()["items"] == res.dump(camel_case=True)

    def test_access_properties(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.list(external_id_prefix="P")
        assert res[0].name == "Pump"
        assert res[0].description == "guess"
        assert res[0].external_id == "PUMP"
        assert res[0].created_time > 0

    def test_call(self, cognite_client, mock_labels_response):
        list(cognite_client.labels(limit=10))
        calls = mock_labels_response.calls
        assert 1 == len(calls)
        assert {"cursor": None, "limit": 10, "filter": {}} == jsgz_load(calls[0].request.body)

    def test_create_single(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.create(LabelDefinition(external_id="1", name="my_label", description="text"))
        assert isinstance(res, LabelDefinition)
        assert mock_labels_response.calls[0].response.json()["items"][0] == res.dump(camel_case=True)
        assert {"items": [{"externalId": "1", "name": "my_label", "description": "text"}]} == jsgz_load(
            mock_labels_response.calls[0].request.body
        )

    def test_create_multiple(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.create([LabelDefinition(external_id="1"), LabelDefinition(external_id="2")])
        assert isinstance(res, LabelDefinitionList)
        assert mock_labels_response.calls[0].response.json()["items"] == res.dump(camel_case=True)
        assert {"items": [{"externalId": "1"}, {"externalId": "2"}]} == jsgz_load(
            mock_labels_response.calls[0].request.body
        )

    def test_delete_single(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.delete(external_id="PUMP")
        assert {"items": [{"externalId": "PUMP"}]} == jsgz_load(mock_labels_response.calls[0].request.body)
        assert res is None

    def test_delete_multiple(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.delete(external_id=["PUMP", "VALVE"])
        assert {"items": [{"externalId": "PUMP"}, {"externalId": "VALVE"}]} == jsgz_load(
            mock_labels_response.calls[0].request.body
        )
        assert res is None

    def test_create_labels_using_wrong_type(self, cognite_client):
        with pytest.raises(TypeError):
            cognite_client.labels.create(Label(external_id="1", name="my_label"))
        with pytest.raises(TypeError):
            cognite_client.labels.create([Label(external_id="1", name="my_label")])

    def test_load_list(self):
        assert Label._load_list(None) == None
        labels = [{"externalId": "a"}, "b", Label("c"), LabelDefinition("d")]
        assert Label._load_list(labels) == [Label("a"), Label("b"), Label("c"), Label("d")]

    def test_list_with_dataset_ids(self, cognite_client, mock_labels_response):
        res = cognite_client.labels.list(data_set_ids=[123], data_set_external_ids=["x"])
        assert res[0].data_set_id == 1
        assert [{"id": 123}, {"externalId": "x"}] == jsgz_load(mock_labels_response.calls[0].request.body)["filter"][
            "dataSetIds"
        ]
