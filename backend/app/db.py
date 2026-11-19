import json
import logging
import os
import socket
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from app.config import settings

logger = logging.getLogger("nurseshift.db")


class LocalDocumentSnapshot:
    """Firestore-compatible DocumentSnapshot for local fallback mode."""

    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]) -> None:
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if self._data is None:
            return None
        return json.loads(json.dumps(self._data))


class LocalDocumentReference:
    """Firestore-compatible DocumentReference for local fallback mode."""

    def __init__(
        self, client: "LocalFirestoreClient", collection_name: str, doc_id: str
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self.id = doc_id

    def get(self) -> LocalDocumentSnapshot:
        col = self._client._store.get(self._collection_name, {})
        return LocalDocumentSnapshot(self.id, col.get(self.id))

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        col = self._client._store.setdefault(self._collection_name, {})
        if merge and self.id in col and isinstance(col[self.id], dict):
            col[self.id].update(json.loads(json.dumps(data)))
        else:
            col[self.id] = json.loads(json.dumps(data))
        self._client._persist()

    def update(self, data: Dict[str, Any]) -> None:
        col = self._client._store.setdefault(self._collection_name, {})
        if self.id not in col:
            raise KeyError(f"Document {self._collection_name}/{self.id} does not exist")
        col[self.id].update(json.loads(json.dumps(data)))
        self._client._persist()

    def delete(self) -> None:
        col = self._client._store.get(self._collection_name, {})
        if self.id in col:
            del col[self.id]
            self._client._persist()


class LocalCollectionReference:
    """Firestore-compatible CollectionReference for local fallback mode."""

    def __init__(self, client: "LocalFirestoreClient", name: str) -> None:
        self._client = client
        self.id = name

    def document(self, doc_id: Optional[str] = None) -> LocalDocumentReference:
        if not doc_id:
            doc_id = uuid.uuid4().hex[:20]
        return LocalDocumentReference(self._client, self.id, doc_id)

    def stream(self) -> Iterator[LocalDocumentSnapshot]:
        col = self._client._store.get(self.id, {})
        for doc_id, data in list(col.items()):
            yield LocalDocumentSnapshot(doc_id, data)


class LocalFirestoreClient:
    """Fallback Firestore-compatible client backed by a local JSON file."""

    is_emulator_fallback = True

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._storage_path = storage_path or Path("/tmp/nurseshift_firestore_fallback.json")
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self._storage_path.exists():
            try:
                self._store = json.loads(self._storage_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Could not load local fallback store: %s", exc)
                self._store = {}

    def _persist(self) -> None:
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._storage_path.write_text(
                json.dumps(self._store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Could not persist local fallback store: %s", exc)

    def collection(self, name: str) -> LocalCollectionReference:
        return LocalCollectionReference(self, name)


_db_client: Any = None
_db_mode: str = "uninitialized"


def _is_emulator_reachable(host_port: str, timeout: float = 1.5) -> bool:
    try:
        host, port_str = host_port.split(":")
        port = int(port_str)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def init_db() -> Any:
    """Initialize connection to Firestore (Emulator or GCP) with safe fallback."""
    global _db_client, _db_mode
    if _db_client is not None:
        return _db_client

    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST", settings.firestore_emulator_host)
    if emulator_host:
        os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host

    if emulator_host and _is_emulator_reachable(emulator_host):
        try:
            from google.auth.credentials import AnonymousCredentials
            from google.cloud import firestore

            _db_client = firestore.Client(
                project=settings.google_cloud_project,
                credentials=AnonymousCredentials(),
            )
            _db_mode = f"firestore-emulator ({emulator_host})"
            logger.info("Connected to Firestore Emulator at %s", emulator_host)
            return _db_client
        except Exception as exc:
            logger.warning("Failed to init Firestore Emulator client: %s", exc)

    logger.warning(
        "Firestore Emulator at '%s' is not reachable; using LocalFirestoreClient fallback.",
        emulator_host,
    )
    fallback_path = Path(__file__).resolve().parent.parent / ".local_firestore_data.json"
    _db_client = LocalFirestoreClient(storage_path=fallback_path)
    _db_mode = "local-firestore-fallback"
    return _db_client


def get_db() -> Any:
    """Return active Firestore client instance."""
    global _db_client
    if _db_client is None:
        return init_db()
    return _db_client


def get_db_mode() -> str:
    """Return human-readable description of active database connection mode."""
    if _db_client is None:
        init_db()
    return _db_mode
