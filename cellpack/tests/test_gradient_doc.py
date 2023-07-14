from cellpack.autopack.DBHandler import GradientDoc
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_should_write_with_no_existing_doc():
    gradient_doc = GradientDoc({"name": "test_grad_name", "test_key": "test_value"})
    doc, doc_id = gradient_doc.should_write(mock_db, "test_grad_name")
    assert doc_id is None
    assert doc is None


def test_should_write_with_existing_doc():
    existing_doc = {"name": "test_grad_name", "test_key": "test_value"}
    mock_db.data = existing_doc
    gradient_doc = GradientDoc({"name": "test_grad_name", "test_key": "test_value"})

    doc, doc_id = gradient_doc.should_write(mock_db, "test_grad_name")
    assert doc_id is not None
    assert doc is not None
