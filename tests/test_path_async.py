from sfapi_client._async.path import RemotePath


def test_concat():
    a = RemotePath("/a")
    b = RemotePath("b")
    c = "c"

    new_path = a / b
    assert isinstance(new_path, RemotePath)
    assert new_path.name == "b"
    assert new_path.group is None
    assert str(new_path) == "/a/b"

    new_path = c / b
    assert isinstance(new_path, RemotePath)
    assert new_path.name == "b"
    assert new_path.group is None
    assert str(new_path) == "c/b"
