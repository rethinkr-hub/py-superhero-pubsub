import pyarrow as pa


# Parquet Schema
SCHEMA_GAME_META_PQ = pa.schema({
    'game_token': pa.utf8(),
    'user_token': pa.utf8(),
    'superhero_id': pa.uint16(),
})

SCHEMA_GAME_PODIUM_PQ = pa.schema({
    'game_token': pa.utf8(),
    'user_token': pa.utf8(),
    'rounds': pa.uint16(),
    'rank': pa.uint8(),
    'damage_delivered': pa.uint64(),
    'damage_received': pa.uint64(),
})