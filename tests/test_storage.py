from cv_bot.storage import CVStore


def test_language_and_photo_lifecycle(tmp_path) -> None:
    store = CVStore(tmp_path)
    user_id = 42

    store.save_language(user_id, "fa")
    assert store.load_language(user_id) == "fa"

    draft_photo = store.draft_photo_path(user_id)
    draft_photo.write_bytes(b"photo")
    final_path = store.finalize_photo(user_id, has_photo=True)

    assert final_path == str(store.photo_path(user_id))
    assert store.photo_path(user_id).read_bytes() == b"photo"
    assert not draft_photo.exists()

    store.delete(user_id)
    assert store.load_language(user_id) == ""
    assert not store.photo_path(user_id).exists()
