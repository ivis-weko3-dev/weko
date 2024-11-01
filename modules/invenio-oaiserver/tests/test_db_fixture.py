def test_db_fixture(db):
    """Test if the db fixture is set up correctly."""
    assert db is not None