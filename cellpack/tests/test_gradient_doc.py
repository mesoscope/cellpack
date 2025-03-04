from cellpack.autopack.DBRecipeHandler import GradientDoc, DataDoc
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_check_doc_existence_for_gradient():
    data_doc = DataDoc()
    gradient_doc = {
        "nucleus_surface_gradient": {
            "mode": "surface",
            "name": "nucleus_surface_gradient",
        }
    }

    test_data = {
        "doc": gradient_doc,
        "dedup_hash": data_doc.generate_hash({"doc": gradient_doc}),
    }

    result = mock_db.check_doc_existence("gradients", test_data)
    assert result is None

    existing_doc = mock_db._existing_doc[0]
    assert existing_doc["dedup_hash"] == test_data["dedup_hash"]
