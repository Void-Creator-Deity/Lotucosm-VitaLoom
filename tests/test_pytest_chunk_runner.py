from __future__ import annotations

from tools.run_pytest_chunked import build_chunks


def test_chunks_preserve_module_order_and_bound_size() -> None:
    ids = [
        "tests/test_a.py::test_1",
        "tests/test_a.py::test_2",
        "tests/test_b.py::test_3",
        "tests/test_c.py::test_4",
        "tests/test_c.py::test_5",
    ]

    chunks = build_chunks(ids, max_tests=3)

    assert [(chunk.modules, chunk.test_count) for chunk in chunks] == [
        (("tests/test_a.py", "tests/test_b.py"), 3),
        (("tests/test_c.py",), 2),
    ]


def test_chunk_size_must_be_positive() -> None:
    try:
        build_chunks(["tests/test_a.py::test_1"], max_tests=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("non-positive chunk size was accepted")
