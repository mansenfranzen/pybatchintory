from pybatchintory.config.settings import Settings

settings = Settings(
    INVENTORY_CONN="sqlite:///backend.db",
    META_CONN="sqlite:///meta.db",
    META_TABLE_NAME="meta_data"
)
