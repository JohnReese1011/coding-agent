def test_embedding_collection_is_provider_model_specific(monkeypatch):
    from coding_agent import settings

    monkeypatch.delenv("MILVUS_COLLECTION", raising=False)
    name = settings.milvus_collection_name()
    assert name.startswith("code_chunks_")
    assert settings.EMBEDDING_PROVIDER in name
    assert settings.EMBEDDING_MODEL.lower().replace("-", "_")[:10] in name


def test_explicit_milvus_collection_overrides_default(monkeypatch):
    from coding_agent.settings import milvus_collection_name

    monkeypatch.setenv("MILVUS_COLLECTION", "my_existing_collection")
    assert milvus_collection_name() == "my_existing_collection"
